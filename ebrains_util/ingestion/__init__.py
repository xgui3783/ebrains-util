import sys
from io import BytesIO
import time

import click
from ebrains_ingestion.workflow_template import ls as wft_ls, show as wft_show, _find as _wft_find
from ebrains_ingestion.workflow import submit as wft_submit, get_status as wft_get_status

from ..iam import get_current_token

@click.group()
def ing():
    """Ingestion (beta)"""
    pass

@click.command()
@click.argument("name", required=False, type=str)
def ls(name: str = None):
    """Show all ingestion pipelines. If name provided, show detail of one pipeline"""
    if name is None:
        wft_ls()
        return
    wft_show(name=name)


def _cast_value(key: str, value: str, type_: str):
    """Cast a raw string arg value to the type declared by the workflow template."""
    if type_ == "number":
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                raise click.BadParameter(f"{value!r} is not a number", param_hint=key)
    if type_ == "integer":
        try:
            return int(value)
        except ValueError:
            raise click.BadParameter(f"{value!r} is not an integer", param_hint=key)
    if type_ == "boolean":
        if value.lower() in ("true", "1", "yes"):
            return True
        if value.lower() in ("false", "0", "no"):
            return False
        raise click.BadParameter(f"{value!r} is not a boolean", param_hint=key)
    return value


def _validate_and_cast(name: str, spec_dict: dict):
    """Validate spec_dict against the workflow template and cast values to declared types."""
    found = _wft_find(name=name)
    if len(found) == 0:
        raise click.ClickException(f"Workflow template {name!r} not found")
    if len(found) > 1:
        raise click.ClickException(f"Multiple workflow templates found for {name!r}")
    tmpl, = found
    properties = tmpl.get("properties", {})
    required = tmpl.get("required", [])

    missing = [r for r in required if r not in spec_dict]
    if missing:
        raise click.ClickException(f"Missing required params: {', '.join(missing)}")

    casted = {}
    for key, value in spec_dict.items():
        prop = properties.get(key)
        if prop is None:
            print(f"warning: unknown param {key!r} for workflow {name!r}", file=sys.stderr)
            casted[key] = value
            continue
        casted[key] = _cast_value(key, value, prop.get("type", "unknown"))
    return casted


def _parse_args(args: tuple[str, ...]):
    d = {}
    i = 0
    while i < len(args):
        tok = args[i]
        if tok.startswith("--"):
            if "=" in tok:
                k, v = tok[2:].split("=", 1)
                d[k] = v
                i += 1
            else:
                d[tok[2:]] = args[i + 1]
                i += 2
        else:
            i += 1
    return d

@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
))
@click.option("--prov", "-p", help="Track provenance.", is_flag=True, )
@click.option("--follow", "-f", help="Follow workflow progress.", is_flag=True, )
@click.argument("name", required=True, type=str, )
@click.argument("specs", nargs=-1)
def submit(name: str, specs, *, follow:bool=False, prov: bool=False):
    """Submit a workflow. use <workflow_name> --key1 value1 --key2 value2"""
    token = get_current_token()
    spec_dict = _parse_args(specs)
    spec_dict = _validate_and_cast(name, spec_dict)

    print(f"submitting {name=}, {spec_dict=}", file=sys.stderr)
    result = wft_submit(name, track_provenance=prov, token=token.token, **spec_dict)
    print("Submission successful")
    if follow:
        while True:
            status_json = wft_get_status(result['id'])
            transactions = status_json["transactions"]
            # clear screen (\033[2J) and move cursor to home (\033[H)
            sys.stdout.write("\033[2J\033[H")
            print(f"status for {result['id']}")

            steps = status_json.get("steps", [])
            step_dict = {
                step["job_id"]: step["name"]
                for step in steps
            }

            for tr in transactions:
                timestamp = tr['timestamp']
                msg = ""
                if job_id := tr.get("job_id"):
                    msg = f"{step_dict.get(job_id, 'unknownjob:' + job_id)} {tr.get('job_status', 'unknown status')}"
                else:
                    msg = f"workflow {tr.get('wf_status')}"
                print(f"{timestamp}: {msg}")
            sys.stdout.flush()
            time.sleep(1)
            
    


ing.add_command(ls, "ls")
ing.add_command(submit, "submit")