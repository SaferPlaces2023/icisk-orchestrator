import os

import nbformat as nbf
import streamlit as st



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
    
    
def dialog_notebook_code(dialog_title: str, notebook_code: str):
    
    @st.dialog(dialog_title, width="large")
    def show_ipynb_code(notebook_code: str):
        notebook = nbf.reads(notebook_code, as_version=4)
        for cell in notebook.cells:
            if cell.cell_type == 'code':
                st.code(cell.source, language='python')
            elif cell.cell_type == 'markdown':
                st.markdown(cell.source)
        if st.button("Close"):
            st.rerun() 
    
    show_ipynb_code(notebook_code)