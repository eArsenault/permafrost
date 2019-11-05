import json
import base64
import os
from textwrap import dedent as d
from datetime import datetime

import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_table
from dash.exceptions import PreventUpdate

import flask
import pandas as pd
import plotly.graph_objs as go


# running directly with Python
if __name__ == '__main__':
    from utils.app_standalone import run_standalone_app

def remove_outlier(df_in, col_name):
    q1 = df_in[col_name].quantile(0.25)
    q3 = df_in[col_name].quantile(0.75)
    iqr = q3-q1 #Interquartile range
    fence_low  = q1-1.5*iqr
    fence_high = q3+1.5*iqr
    df_out = df_in.loc[(df_in[col_name] > fence_low) & (df_in[col_name] < fence_high)]
    return df_out

def preprocess(df_in): #
    criteria = df_in['Time'].str.startswith('0')
    df_in['Time'][criteria] = '0' + df_in['Time'][criteria]
    df_in['Time'] = pd.to_datetime(df_in['Date'] + ' ' + df_in['Time'], format = "%m/%d/%Y %H:%M:%S")
    df_in = df_in.drop(columns="Date")
    return df_in

#def plot_extrema():
def trumpet_curve(df, col_time):
    filtered_df = df[df.columns[~df.columns.isin([col_time])]]
    print(filtered_df)

    maxindex = filtered_df[filtered_df.max().idxmax()].idxmax()
    minindex = filtered_df[filtered_df.min().idxmin()].idxmin()

    print(filtered_df[filtered_df.min().idxmin()].idxmin())
    #print(filtered_df.iloc[maxindex])
    #print(filtered_df.iloc[minindex])
    return maxindex,minindex

def table_from_raw(raw_data,table_id,max_rows=20,skiprows=0,skipcols=0,header=False):
    data = raw_data[skiprows:min(len(raw_data),max_rows)]
    data = [data_row[skipcols:] for data_row in data]
    indexes = range(len(data[0]))

    if header:
        columns = [{"name": i, "id": i} for i in data[0]]
        data = data[1:]
    else:
        columns = [{"name": "col{}".format(i), "id": "col{}".format(i)} for i in indexes]

    return dash_table.DataTable(
        id=table_id,

        data = [{columns[i]["name"]: data_row[i] for i in indexes} for data_row in data],
        columns = columns,
        style_table={'maxHeight':'550px','overflowY':'scroll'}
    )

def dataframe_from_raw(raw_data,skiprows=0,skipcols=0,header=False):
    data = raw_data[skiprows:]
    data = [data_row[skipcols:] for data_row in data]
    indexes = range(len(data[0]))

    if header:
        columns = [{"name": i, "id": i} for i in data[0]]
        data = data[1:]
    else:
        columns = [{"name": "col{}".format(i), "id": "col{}".format(i)} for i in indexes]
    
    df = pd.DataFrame.from_records(data, columns = columns)
    print(df)

text_style = {
    'color': "#506784",
    'font-family': 'Open Sans'
}

df = pd.read_csv(os.path.join(".","assets","sample_data","Sample_Data_Set.csv"), skiprows=3)
df = preprocess(df)

col_names = [
    'Bead #1(-0.60m)',
    'Bead #2(-0.90m)',
    'Bead #3(-1.20m)',
    'Bead #4(-1.50m)',
    'Bead #5(-1.80m)',
    'Bead #6(-2.10m)',
    'Bead #7(-2.40m)',
]

col_colours = [
    'deepskyblue',
    'dimgray',
    'red',
    'blue',
    'green',
    'yellow',
    'brown'
]

for name in  col_names:
    df = remove_outlier(df,name)

def description():
    return 'View multiple sequence alignments of genomic or protenomic sequences.'


def header_colors():
    return {
        'bg_color': '#0C4142',
        'font_color': 'white',
    }


def layout():
    return html.Div(id='alignment-body', className='app-body', children=[
        html.Div(children=[
            html.Div(id='alignment-control-tabs', className='control-tabs', children=[
                dcc.Tabs(
                    id='alignment-tabs', value='what-is',
                    children=[
                        dcc.Tab(
                            label='About',
                            value='what-is',
                            children=html.Div(className='control-tab', children=[
                                html.H4(
                                    className='what-is',
                                    children='What is PermaPortal?'
                                ),
                                html.P(
                                    """
                                    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
                                    """
                                ),
                                html.P(
                                    """
                                    Source code available at: 
                                    https://github.com/eArsenault/permafrost
                                    """
                                ),
                            ])
                        ),
                        dcc.Tab(
                            label='Add Data',
                            value='alignment-tab-select',
                            children=html.Div(className='control-tab', children=[

                                html.Div(className='app-controls-block', children=[
                                    html.Div(className='fullwidth-app-controls-name',
                                             children="Upload your own dataset (.csv)"),
                                    html.A(
                                        html.Button(
                                            "Download sample data",
                                            className='control-download'
                                        ),
                                        href="/assets/sample_data/Sample_Data_Set.csv",
                                        download="Sample_Data_Set.csv",
                                    ),
                                    html.Div(id='alignment-file-upload-container', children=[
                                        dcc.Upload(
                                            id='alignment-file-upload',
                                            className='control-upload',
                                            children=html.Div([
                                                "Drag and drop files or select files."
                                            ]),
                                        )
                                    ])
                                ]),

                                html.Div(className='app-controls-block', children=[
                                    html.Label('Rows to skip:'),
                                    dcc.Input(id='skiprows_option',value=0, type='number'),

                                    html.Label('Columns to skip:'),
                                    dcc.Input(id='skipcols_option',value=0, type='number'),

                                    dcc.Checklist(
                                        id='header_option',
                                        options=[
                                            {'label': 'My data has a header', 'value': 'YES'},
                                        ],
                                        value=[],
                                        style={'padding':'5px'}
                                    )  
                                ]),
                                dcc.RadioItems(
                                    id='view-radio',
                                    options=[
                                        {'label': 'Table view', 'value': 'table'},
                                        {'label': 'Graph view', 'value': 'graph'},
                                    ],
                                    value='table'
                                )
                            ])
                        )
                    ],
                ),
            ]),
        ]),
        html.Div(id='permafrost-graph-panel', children=[ 
            html.Div(id='permafrost-graph-grid',className='permafrost-graph-grid',children=[ #dcc.Loading(className='dashbio-loading', children=
                html.Div(id='permafrost-main-graph',className='permafrost-main-graph',children=[
                    dcc.Graph(
                            id = 'graph-temptime',
                            hoverData={"points": [{"x": datetime.strptime("2010-01-01 00:00","%Y-%m-%d %H:%M")}]}
                    )
                ]),
                html.Div(id='permafrost-label-first',className='permafrost-label-first',children=[
                    html.Label('Start Date (MM/DD/YYYY)'),
                    dcc.Input(id = 'input-text',value='09/25/1999', type='text'),
                ]),
                html.Div(id='permafrost-label-second',className='permafrost-label-second',children=[
                    html.Label('End Date (MM/DD/YYYY)'),
                    dcc.Input(id = 'end-text',value='08/29/2010', type='text'),
                ]),
                html.Div(id='permafrost-sub-graph',className='permafrost-sub-graph',children=[
                    dcc.Graph(
                        id = 'graph-depthtemp',
                    )
                ]),
            ]),
        ]),
        dcc.Store(id='permafrost-data-store'),
    ])


def callbacks(_app):

    @_app.callback(
        Output('permafrost-table','children'),
        [Input('permafrost-data-store', 'modified_timestamp'),
         Input('skiprows_option', 'value'),
         Input('skipcols_option', 'value'),
         Input('header_option', 'value')],
        [State('permafrost-data-store', 'data')]
    )
    def update_table(ts, skiprows, skipcols, header, data):  
        try: 
            print(data[:5]) 
        except: 
            print(data) 

        if ts is None or data == {}:
            raise PreventUpdate
        
        if header == ['YES']:
            header = True
        else:
            header = False

        return table_from_raw(data,table_id='data-table',skiprows=skiprows,skipcols=skipcols,header=header)

    # Handle file upload/selection into data store
    @_app.callback(
        Output('permafrost-data-store', 'data'),
        [Input('alignment-file-upload', 'contents'),
         Input('alignment-file-upload', 'filename')]
    )
    def update_storage(contents, filename):

        if (contents is not None) and ('csv' in filename):
            content_type, content_string = contents.split(',')
            content = base64.b64decode(content_string).decode('UTF-8')
            content = [text.split(",") for text in content.replace("\r","").split("\n")]
            print(content[:5])
        else:
            content = {}

        return content

    @_app.callback(
        Output('graph-temptime', 'figure'),
        [Input('input-text', 'value'),
         Input('end-text','value')]
    )
    def update_figure(start_str,end_str):

        start_datetime = datetime.strptime(start_str,'%m/%d/%Y') #add a try  catch loop
        end_datetime = datetime.strptime(end_str,'%m/%d/%Y')

        filtered_df = df[(df['Time'] < end_datetime) & (df['Time'] > start_datetime)]
        traces = []
        for i in range(7): #avoid magic numbers
            traces.append(go.Scatter(
                x=filtered_df['Time'],
                y=filtered_df[col_names[i]],
                opacity=0.8,
                line_color=col_colours[i],
                name=col_names[i]
            ))
        
        traces.append(go.Scatter(
            x=[filtered_df['Time'].min(),filtered_df['Time'].max()],
            y=[0,0],
            line={'color':'black','dash':'dash'},
            name="Freezing Point",
            opacity=0.5,
        ))

        return {
            'data': traces,
            'layout': go.Layout(
                margin={'l': 40, 'b': 40, 't': 40, 'r': 40},

                legend_orientation='h',
                hovermode='closest',
                yaxis={'zeroline':False}
            )
        }

    @_app.callback(
        Output('graph-depthtemp', 'figure'),
        [Input('graph-temptime', 'hoverData')]
    )
    def display_depthdata(hoverData):
        df_noTime = df[df.columns[~df.columns.isin(['Time'])]]
        filtered_df = df_noTime.loc[df['Time'] == hoverData['points'][0]['x']]
        
        maxindex, minindex = trumpet_curve(df,"Time")
        print(minindex)
        #print(df.iloc[minindex])
        traces = [go.Scatter(
            x=filtered_df.squeeze(),
            y=[-0.60,-0.90,-1.20,-1.50,-1.80,-2.10,-2.40],
            opacity=0.8,
            line_color=col_colours[0],
            name = "Ground Depth"
        ),
        go.Scatter(
            x=[0,0],
            y=[-2.4,-.6],
            line={'color':'black','dash':'dash'},
            name="Freezing Point",
            opacity=0.5,
        ),
        go.Scatter(
            x=df_noTime.loc[maxindex],
            y=[-0.60,-0.90,-1.20,-1.50,-1.80,-2.10,-2.40],
            line={'color':'black','dash':'dash'},
            name="Max",
            opacity=0.5,
        ),
        go.Scatter(
            x=df_noTime.loc[minindex],
            y=[-0.60,-0.90,-1.20,-1.50,-1.80,-2.10,-2.40],
            line={'color':'black','dash':'dash'},
            name="Min",
            opacity=0.5,
        )]

        return {
            'data': traces,
            'layout': go.Layout(
                margin={'l': 40, 'b': 40, 't': 40, 'r': 40},
                hovermode='closest',
                xaxis={'range':[-30,15], 'zeroline': False},

                legend_orientation='h',
                showlegend=True,
            )
        }

    @_app.callback(
        Output('permafrost-graph-panel','children'),
        [Input('alignment-tabs', 'value'),
         Input('view-radio', 'value')],
        [State('skiprows_option', 'value'),
         State('skipcols_option', 'value'),
         State('header_option', 'value'),
         State('permafrost-data-store', 'data')]
    )
    def render_content(tab,radio,skiprows,skipcols,header,data):
        if tab == 'what-is':
            return dcc.Graph(id='permafrost-map',
                    figure={
                        'data':[go.Scattermapbox(
                            lat = ['44.2250'],
                            lon = ['-76.4951'],
                            
                            mode = 'markers',
                            marker = go.Marker(
                                size = 11
                            ),

                            name="Sites",
                            text=["Test Site #1"],
                            #hoverinfo='text',
                        )],
                        'layout': go.Layout(
                            margin={'l': 10, 'b': 10, 't': 10, 'r': 10},
                            autosize = True,
                            hovermode = 'closest',
                            geo = dict(
                                projection = dict(type = "equirectangular"),
                                ),
                            mapbox = dict(
                                center = dict(
                                    lat = 44.2250,
                                    lon = -76.4951
                                    ),
                                pitch = 0,
                                zoom = 8,
                                style = 'open-street-map'
                            )
                        )
                    }
            )   
        elif radio == 'table':
            return html.Div(id='permafrost-table',children=[
                html.P("Please add a dataset.")
            ])

        else:
            print(data[:5])
            dataframe_from_raw(data,skiprows=skiprows,skipcols=skipcols,header=header)
            return html.P('AH')
            
    @_app.callback(
        Output('click-data', 'children'),
        [Input('permafrost-map', 'clickData')])
    def display_click_data(clickData):
        return json.dumps(clickData, indent=2)
        
# only declare app/server if the file is being run directly
if 'DASH_PATH_ROUTING' in os.environ or __name__ == '__main__':
    app = run_standalone_app(layout, callbacks, header_colors, __file__)
    server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
