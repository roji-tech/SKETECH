#!/usr/bin/env python
import os
import django
from django.apps import apps
from graphviz import Digraph

def setup_django():
    """Set up Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CONFIG.settings')
    django.setup()

def generate_schema(output_file='schema', view=True):
    """Generate a DB schema diagram using Graphviz"""
    # Initialize the graph
    dot = Digraph(
        comment='Database Schema',
        graph_attr={
            'rankdir': 'TB',
            'splines': 'polyline',
            'nodesep': '0.6',
            'ranksep': '0.8',
        },
        node_attr={
            'shape': 'box',
            'style': 'filled',
            'fillcolor': 'lightblue',
            'fontname': 'Arial',
            'fontsize': '10',
        },
        edge_attr={
            'fontname': 'Arial',
            'fontsize': '8',
        }
    )

    # Get all models
    models = apps.get_models()
    
    # Add nodes (tables)
    for model in models:
        # Skip proxy models
        if model._meta.proxy:
            continue
            
        # Create table header
        table_name = model._meta.db_table
        label = f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
        label += f'<TR><TD BGCOLOR="#4F81BD" COLSPAN="2"><FONT COLOR="white">{table_name}</FONT></TD></TR>'
        
        # Add primary key field
        pk = model._meta.pk
        label += f'<TR><TD PORT="{pk.name}" ALIGN="LEFT"><B>{pk.name}</B></TD><TD>{pk.get_internal_type()}</TD></TR>'
        
        # Add other fields
        for field in model._meta.fields:
            if field.primary_key:
                continue
            label += f'<TR><TD PORT="{field.name}" ALIGN="LEFT">{field.name}</TD><TD>{field.get_internal_type()}</TD></TR>'
        
        label += '</TABLE>>'
        
        dot.node(table_name, label, shape='plaintext')
    
    # Add edges (relationships)
    for model in models:
        if model._meta.proxy:
            continue
            
        for field in model._meta.get_fields():
            if field.many_to_one and field.related_model:
                # Many-to-one relationship
                dot.edge(
                    field.related_model._meta.db_table,
                    model._meta.db_table,
                    label=f'1..*',
                    arrowhead='crow',
                    arrowtail='none'
                )
            elif field.one_to_many:
                # One-to-many relationship
                dot.edge(
                    model._meta.db_table,
                    field.related_model._meta.db_table,
                    label=f'1..*',
                    arrowhead='crow',
                    arrowtail='none'
                )
            elif field.many_to_many and not field.auto_created:
                # Many-to-many relationship
                dot.edge(
                    model._meta.db_table,
                    field.related_model._meta.db_table,
                    label=f'*..*',
                    dir='both',
                    arrowhead='crow',
                    arrowtail='crow'
                )
    
    # Save and render
    dot.format = 'png'
    dot.render(output_file, view=view, cleanup=True)
    print(f"Schema diagram generated: {output_file}.png")

if __name__ == '__main__':
    setup_django()
    generate_schema()
