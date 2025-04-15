import os

def tool_args_md_table(args_dict):
    if all([v is None for k,v in args_dict.items()]):
        return ''
    else:
        table = "| Parameter | Value |\n"
        table += "|-----------|--------|\n"
        for key, value in args_dict.items():
            if value is not None:
                table += f"| {key} | {value} |\n"
        return table