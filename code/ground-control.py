# This is the ground control software for the Cakrawala Flight Computer. Developed by Gema Sagara H. 07/2024

from flask import Flask
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output
import dash_daq as daq
import plotly.graph_objs as go
from collections import deque
import time
import random
import math
import numpy as np

server = Flask(__name__)
app = Dash(__name__, server=server, url_base_pathname='/dashboard/')

# Define color scheme
colors = {
    'background': '#1e1f21',
    'text': '#fffcf2',
    'grid': '#292b2e',
    'red': '#f03535',
    'yellow' : '#E8AA42'
}

max_length = 100
times = deque(maxlen=max_length)

gyro_x = deque(maxlen=max_length) # Yaw
gyro_y = deque(maxlen=max_length) # Pitch
gyro_z = deque(maxlen=max_length) # Roll

acc_x = deque(maxlen=max_length)
acc_y = deque(maxlen=max_length)
acc_z = deque(maxlen=max_length)

speed = deque(maxlen=max_length)
pressures = deque(maxlen=max_length)
altitude = 0

app.layout = html.Div(children=[
    html.H1('Cakrawala Ground Control (Simulation)', style={'textAlign': 'center', 'color': colors['text']}),
    html.Div([
        dcc.Graph(id='horiz-scene', className='horiz-scene-container'),
    html.Div([
        html.Div([
        html.Button('Set Launch Site', id='setlaunch-button', className='control-button'),
        html.Button('Launch', id='launch-button', className='control-button'),
        html.Button('ABORT - Reset', id='abort-button', className='control-button'),
    ], className='button-container'),
    # Phase indicators
    html.Div([
        html.Div([
            html.Div([
                html.Span('N / A', className='phase-text'),
            ], className='phase-circle'),
            html.P('Launch', className='phase-label')
        ], className='phase-container'),

        html.Div([
            html.Div([
                html.Span('N / A', className='phase-text'),
            ], className='phase-circle'),
            html.P('Flight', className='phase-label')
        ], className='phase-container'),

        html.Div([
            html.Div([
                html.Span('N / A', className='phase-text'),
            ], className='phase-circle'),
            html.P('Descent', className='phase-label')
        ], className='phase-container'),
    ], className='phase-indicators')
    ], className='middle-control'),
    html.Div([
        html.Div("Rocket Speed", className="graph-title"),
        daq.Gauge(
            id='rocket-speed',
            color={"gradient":True,"ranges":{"green":[0,100],"yellow":[100,200],"red":[200,300]}},
            showCurrentValue=True,
            units="KPH",
            label=" ",
            max=300,
            min=0,
            className='speed-container'
        )
    ], className='gauge-wrapper')
], className='top-row-container'),
    html.Div([
        dcc.Graph(id='topdown-scene', className='topdown-scene-container quarter-width'),
        dcc.Graph(id='yaw-visual', className='yaw-visual-container quarter-width'),
        dcc.Graph(id='pitch-visual', className='yaw-visual-container quarter-width'),
        html.Div([
    html.Div("Raw Telemetry", className="graph-title"),
    dash_table.DataTable(
        id='telemetry-table',
        columns=[
            {"name": "Sensor", "id": "sensor"},
            {"name": "Value", "id": "value"},
            {"name": "Unit", "id": "unit"}
        ],
        style_header={
            'backgroundColor': 'rgba(50, 50, 50, 1)',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_cell={
            'backgroundColor': 'rgba(30, 30, 30, 1)',
            'color': 'white',
            'textAlign': 'center'
        },
        style_table={'height': '100%', 'overflowY': 'auto'},
        style_data={
            'height': 'auto',  # Allow row height to adjust automatically
            'lineHeight': '15px'  # Adjust line height for better spacing
        }
    )
], className='telemetry-table-container quarter-width')
    ], className='graph-row'),
    dcc.Interval(
        id='graph-update',
        interval=500,  # update every 0.5 seconds
        n_intervals=0
    )
])

def horizGraph():
    x_range = max(25, max(abs(max(acc_x)), abs(min(acc_x))) * 1.1)
    y_range = max(25, max(abs(max(acc_y)), abs(min(acc_y))) * 1.1)
    
    trace_path = go.Scatter(
        x=list(acc_x),
        y=list(acc_y),
        mode='lines',
        line=dict(
            color=colors['red'],
            width=2,
        ),
        name='Path'
    )
    
    trace_current = go.Scatter(
        x=[acc_x[-1]] if acc_x else [0],
        y=[acc_y[-1]] if acc_y else [0],
        mode='markers',
        marker=dict(
            size=10,
            color=colors['yellow'],
            symbol='circle'
        ),
        name='Current Position'
    )
    
    trace_start = go.Scatter(
        x=[0],
        y=[0],
        mode='markers',
        marker=dict(
            size=15,
            color=colors['red'],
            symbol='circle'
        ),
        name='Start Position'
    )

    return {
        'data': [trace_path, trace_current, trace_start],
        'layout': go.Layout(
            title=dict(
                text='Scene, Horizontal',
                font=dict(color=colors['text'])
            ),
            xaxis=dict(
                title='X Travel (m)',
                color=colors['text'],
                gridcolor=colors['grid'],
                range=[-x_range, x_range],
                zeroline=True,
                zerolinecolor=colors['grid']
            ),
            yaxis=dict(
                title='Altitude (m)',
                color=colors['text'],
                gridcolor=colors['grid'],
                range=[0, y_range],  # Altitude starts from 0
                zeroline=True,
                zerolinecolor=colors['grid']
            ),
            paper_bgcolor=colors['background'],
            plot_bgcolor=colors['background'],
            showlegend=False,
            margin=dict(l=50, r=50, t=50, b=50),
            height=300
        )
    }

def topDownGraph():
    # Calculate the range based on the maximum absolute value from both X and Y
    max_abs_value = max(
        50,  # Minimum range
        max(abs(max(acc_x)), abs(min(acc_x)),
            abs(max(acc_z)), abs(min(acc_z))) * 1.1
    )
    
    trace_path = go.Scatter(
        x=list(acc_x),
        y=list(acc_z),
        mode='lines',
        line=dict(
            color=colors['red'],
            width=2,
        ),
        name='Path'
    )
    
    trace_current = go.Scatter(
        x=[acc_x[-1]] if acc_x else [0],
        y=[acc_z[-1]] if acc_z else [0],
        mode='markers',
        marker=dict(
            size=10,
            color=colors['yellow'],
            symbol='circle'
        ),
        name='Current Position'
    )
    
    trace_start = go.Scatter(
        x=[0],
        y=[0],
        mode='markers',
        marker=dict(
            size=10,
            color=colors['red'],
            symbol='circle'
        ),
        name='Start Position'
    )

    return {
        'data': [trace_path, trace_current, trace_start],
        'layout': go.Layout(
            title=dict(
                text='Scene, Top Down',
                font=dict(color=colors['text'])
            ),
            xaxis=dict(
                title='X Travel (m)',
                color=colors['text'],
                gridcolor=colors['grid'],
                range=[-max_abs_value, max_abs_value],
                zeroline=True,
                zerolinecolor=colors['grid']
            ),
            yaxis=dict(
                title='Z Travel (m)',
                color=colors['text'],
                gridcolor=colors['grid'],
                range=[-max_abs_value, max_abs_value],
                zeroline=True,
                zerolinecolor=colors['grid'],
                scaleanchor="x",
                scaleratio=1,
            ),
            paper_bgcolor=colors['background'],
            plot_bgcolor=colors['background'],
            margin=dict(l=50, r=50, t=50, b=50),
            autosize=True,
            showlegend=False
        )
    }

def gyroVisual(gyro):
    # Create a rectangle with an extra point on the top center for the marker
    x = np.array([-0.5, 0.5, 0.5, -0.5, -0.5, 0])  # Added 0 for the x-coordinate of the marker
    y = np.array([-2, -2, 2, 2, -2, 2])  # Added 2 for the y-coordinate of the marker
    
    # If yaw is an iterable, take the last value
    if hasattr(gyro, '__iter__'):
        gyro = gyro[-1]
    
    # Rotate the rectangle (negative angle for reversed direction)
    theta = np.radians(-gyro)  # Note the negative sign here
    rotation_matrix = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta), np.cos(theta)]
    ])
    
    points = np.column_stack((x, y))
    rotated_points = np.dot(points, rotation_matrix.T)
    
    x_rot, y_rot = rotated_points.T
    
    # Create scatter plot for the rectangle and the marker
    scatter = go.Scatter(
        x=np.append(x_rot[:5], x_rot[5]), 
        y=np.append(y_rot[:5], y_rot[5]),
        fill="toself", 
        fillcolor='#FCCE84', 
        line=dict(color='#FCCE84'),
        mode='markers+lines', 
        marker=dict(color=colors['red'], size=[0]*5 + [20]),
        showlegend=False
    )
    
    return scatter

def raw_telemetry(acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, pressure, speed):
    return [
        {"sensor": "Acc X", "value": f"{acc_x:.2f}", "unit": "m/s²"},
        {"sensor": "Acc Y", "value": f"{acc_y:.2f}", "unit": "m/s²"},
        {"sensor": "Acc Z", "value": f"{acc_z:.2f}", "unit": "m/s²"},
        {"sensor": "Yaw", "value": f"{gyro_x:.2f}", "unit": "°/s"},
        {"sensor": "Pitch", "value": f"{gyro_y:.2f}", "unit": "°/s"},
        {"sensor": "Roll", "value": f"{gyro_z:.2f}", "unit": "°/s"},
        {"sensor": "Pressure", "value": f"{pressure:.2f}", "unit": "hPa"},
        {"sensor": "Speed", "value": f"{speed:.2f}", "unit": "m/s"}
    ]

@app.callback(
    [Output('horiz-scene', 'figure'),
     Output('topdown-scene', 'figure'),
     Output('yaw-visual', 'figure'),
     Output('pitch-visual', 'figure'),
     Output('rocket-speed', 'value'),
     Output('telemetry-table', 'data')],
    [Input('graph-update', 'n_intervals'), Input('setlaunch-button', 'n_clicks')]
)

def update_graphs(n, setlaunch):
    global acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, altitude, speed, pressures

    if setlaunch:
        # Reset all variables to zero
        acc_x.clear()
        acc_y.clear()
        acc_z.clear()
        gyro_x.clear()
        gyro_y.clear()
        gyro_z.clear()
        speed.clear()
        pressures.clear()
        altitude = 0

        # Reinitialize variables with zero
        acc_x.append(0)
        acc_y.append(0)
        acc_z.append(0)
        gyro_x.append(0)
        gyro_y.append(0)
        gyro_z.append(0)
        speed.append(0)
        pressures.append(0)
    
    current_time = time.time()
    times.append(current_time)
    
    # Generate random data for simulation
    altitude = random.uniform(0, 1000)
    speed.append(random.uniform(0, 300))
    
    # Update X & Z Axis accelerometer data
    if not acc_x:
        acc_x.append(0)
        acc_z.append(0)
    else:
        dx = random.uniform(-10, 10)
        dz = random.uniform(-10, 10)
        acc_x.append(acc_x[-1] + dx)
        acc_z.append(acc_z[-1] + dz)
    
    # Update Y Axis accelerometer data
    if not acc_y:
        acc_y.append(0)
    else:
        acc_y.append(altitude)
    
    gyro_x.append(random.uniform(-180, 180))
    gyro_y.append(random.uniform(-180, 180))
    gyro_z.append(random.uniform(-180, 180))
    pressures.append(random.uniform(900, 1100))
    
    # Create horizontal scene graph
    horiz_data = horizGraph()
    horiz_fig = go.Figure(data=horiz_data['data'], layout=horiz_data['layout'])
    
    # Create top-down scene graph
    topdown_data = topDownGraph()
    topdown_fig = go.Figure(data=topdown_data['data'], layout=topdown_data['layout'])
    
    # Yaw & Pitch rocket body visualization
    yaw_fig = go.Figure(data=[gyroVisual(gyro_x[-1])])
    yaw_fig.update_layout(
        title=dict(
                text='Yaw Rotation',
                font=dict(color=colors['text']),
                y=0.95,  # Adjust this value to position the title
                x=0.5,
                xanchor='center',
                yanchor='top'
            ),
        xaxis=dict(range=[-3, 3], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[-3, 3], showgrid=False, zeroline=False, showticklabels=False),
        showlegend=False,
        width=400,
        height=400,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=colors['background'],
        plot_bgcolor=colors['background'],
    )
    
    pitch_fig = go.Figure(data=[gyroVisual(gyro_y[-1])])
    pitch_fig.update_layout(
        title=dict(
                text='Pitch Rotation',
                font=dict(color=colors['text']),
                y=0.95,  # Adjust this value to position the title
                x=0.5,
                xanchor='center',
                yanchor='top'
            ),
        xaxis=dict(range=[-3, 3], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[-3, 3], showgrid=False, zeroline=False, showticklabels=False),
        showlegend=False,
        width=400,
        height=400,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=colors['background'],
        plot_bgcolor=colors['background'],
    )
    
    # Create the raw telemetry table
    telemetry_table = raw_telemetry(
        acc_x[-1], acc_y[-1], acc_z[-1],
        gyro_x[-1], gyro_y[-1], gyro_z[-1],
        pressures[-1], speed[-1]  # Assuming you have a speed variable
    )
    return horiz_fig, topdown_fig, yaw_fig, pitch_fig, speed[-1], telemetry_table

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
