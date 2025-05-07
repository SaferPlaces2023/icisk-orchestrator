import os

import nbformat as nbf
from nbconvert import HTMLExporter

import streamlit as st
import streamlit.components.v1 as components



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
    
    
def dialog_notebook_code(dialog_title: str, notebook_code: str | nbf.NotebookNode):
    
    st.markdown(
        """
        <style>
        div[data-testid="stDialog"] div[role="dialog"]:has(.big-dialog) {
            width: 80vw;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    @st.dialog(dialog_title, width="large")
    def show_ipynb_code(notebook_code: str | nbf.NotebookNode):
        st.html("<span class='big-dialog'></span>")
        
        def convert_notebook_str_to_html(nb_str):
            nb = nbf.reads(nb_str, as_version=4)
            html_exporter = HTMLExporter()
            body, _ = html_exporter.from_notebook_node(nb)
            return body

        notebook_str = nbf.writes(notebook_code, version=4) if isinstance(notebook_code, nbf.NotebookNode) else notebook_code
        html = convert_notebook_str_to_html(notebook_str)
        components.html(html, height=800, scrolling=True)
        
        if st.button("Close"):
            st.rerun() 
    
    show_ipynb_code(notebook_code)
    
    
def css_component(component, key: str, css_dict: dict[str, str], **component_args):
    """
    A function to create a Streamlit component with custom CSS styles.
    
    Parameters:
    - component: The Streamlit component to be styled.
    - key: The key for the component in the Streamlit session state.
    - css_dict: A dictionary containing CSS properties and their values.
    - **component_args: Additional arguments for the component.
    
    Returns:
    - The rendered component with custom CSS styles.
    """
    css = "\n".join([f"{k}: {v};" for k, v in css_dict.items()])
    st.markdown(
        f"""
        <style>
        .st-key-{key} {{
            {css}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    return component(key=key, **component_args)
    