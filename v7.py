import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# --- Load and prepare the data ---
try:
    df = pd.read_csv('ETIMTxnData_2025-9-6_1748.csv')
    df['TICKET_TIME_STAMP'] = pd.to_datetime(df['TICKET_TIME_STAMP'])
    df['Hour'] = df['TICKET_TIME_STAMP'].dt.hour
    df['Time_Interval'] = (df['Hour'] // 3) * 3
    df['Time_Interval_Label'] = df['Time_Interval'].astype(str).str.zfill(2) + '-' + (df['Time_Interval'] + 3).astype(str).str.zfill(2) + ' hrs'
    
except FileNotFoundError:
    print("Error: The file 'ETIMTxnData_2025-9-6_1748.csv' was not found.")
    print("Please make sure the CSV file is in the same directory as the app.py script.")
    df = pd.DataFrame(columns=['DEPOT_NAME', 'CITY_NAME', 'ROUTE_NAME', 'PASSENGER_COUNT', 'FARE_COLLECTED', 'PAYMENT_MODE', 'TICKET_TIME_STAMP', 'Passenger Type'])

# Clean depot options
depot_options = [
    {'label': str(i).strip(), 'value': str(i).strip()}
    for i in df['DEPOT_NAME'].dropna().unique()
    if isinstance(i, str) and str(i).strip() != ''
]

# Clean city options
city_options = [
    {'label': str(i).strip(), 'value': str(i).strip()}
    for i in df['CITY_NAME'].dropna().unique()
    if isinstance(i, str) and str(i).strip() != ''
]

# --- Initialize the Dash App ---
app = Dash(__name__)
server = app.server

# --- Define the Dashboard Layout ---
app.layout = html.Div(
    className="bg-gradient-to-r from-indigo-500 to-blue-600 py-6 px-10 rounded-xxl shadow-md mb-20 flex justify-between items-center",
    style={'backgroundColor': '#eef4f8', 'fontFamily': 'sans-serif'},
    children=[

        html.Img(
            src="/assets/crut-logo.png",  # Make sure the uploaded image is saved as 'crut-logo.png' in the 'assets' folder
            style={
                "height": "70px",
                "width": "70px",
                "borderRadius": "0px",
                "position": "absolute",
                "top": "20px",
                "right": "30px",
                "zIndex": "800"

            }
        ),
        html.H1(
            "CRUT Daily Operations Dashboard",
            className="text-center text-4xl font-bold text-gray-800 mb-8"
        ),

        html.Div(
            className="flex flex-col md:flex-row gap-4 mb-8",
            children=[
                dcc.Dropdown(id='city-dropdown',
                    options=city_options,
                    placeholder="Select City",
                    multi=True,
                    className="flex-1 rounded-lg shadow-sm",
                    style={
                        'backgroundColor': '#fef9c3',  # Light yellow
                        'color': '#92400e',  # Brown text
                        'borderRadius': '8px',
                        'padding': '8px',
                        'fontWeight': 'bold',
                        'border': '1px solid #fde047',
                        "width": "80%"

                    }
                ),
                dcc.Dropdown(
                    id='depot-dropdown',
                    options=depot_options,
                    placeholder="Select Depot",
                    multi=True,
                    className="flex-1 rounded-lg shadow-sm",
                    style={
                        'backgroundColor': '#e0f2fe',  # Light blue
                        'color': '#1e3a8a',  # Dark blue text
                        'borderRadius': '8px',
                        'padding': '8px',
                        'fontWeight': 'bold',
                        'border': '1px solid #60a5fa',
                        "width": "80%"
                    }
                ),
                dcc.Dropdown(
                    id='route-dropdown',
                    options=[],  # Will be populated dynamically
                    placeholder="Select Route",
                    multi=True,
                    className="flex-1 rounded-lg shadow-sm",
                    style={
                        'backgroundColor': '#f0fdf4',  # Light green
                        'color': '#166534',  # Dark green text
                        'borderRadius': '8px',
                        'padding': '8px',
                        'fontWeight': 'bold',
                        'border': '1px solid #86efac',
                        "width": "80%"
                    }
                )
            ]
        ),

        # Cards container with responsive layout and new cards
        html.Div(
            id='cards-container',
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        ),

        # Graphs container
        html.Div(
            className="flex flex-col lg:flex-row gap-6",
            children=[
                html.Div(
                    className="bg-white rounded-xl shadow-lg p-6 flex-1",
                    children=dcc.Graph(id='pie-chart-transaction-type')
                ),
                html.Div(
                    className="bg-white rounded-xl shadow-lg p-6 flex-1",
                    children=dcc.Graph(id='temporal-chart-ridership')
                ),
            ]
        ),
        
        # New section for the Passenger Type chart and ridership distribution chart
        html.Div(
            className="flex flex-col lg:flex-row gap-6 mt-8",
            children=[
                 html.Div(
                    className="bg-white rounded-xl shadow-lg p-6 flex-1",
                    children=dcc.Graph(id='passenger-type-chart')
                ),
                html.Div(
                    className="bg-white rounded-xl shadow-lg p-6 flex-1",
                    children=[
                        html.H3("Ridership Distribution by Hour", className="text-center text-2xl font-semibold text-gray-700 mb-4"),
                        dcc.RangeSlider(
                            id='time-range-slider',
                            min=0,
                            max=24,
                            step=1,
                            value=[6, 18],
                            marks={i: {'label': f'{i}:00', 'style': {'font-size': '12px'}} for i in range(0, 25, 3)},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                        dcc.Graph(id='ridership-area-chart', className="mt-4")
                    ]
                ),
            ]
        ),
    ]
)

# --- Define Callbacks for Interactivity ---
# Callback to dynamically update the route dropdown options
@app.callback(
    [Output('route-dropdown', 'options'),
     Output('route-dropdown', 'value')],
    [Input('depot-dropdown', 'value'),
     Input('city-dropdown', 'value')]
)
def set_route_options(selected_depots, selected_cities):
    filtered_df = df.copy()

    if selected_depots and selected_depots != [None]:
        filtered_df = filtered_df[filtered_df['DEPOT_NAME'].isin(selected_depots)]
    if selected_cities and selected_cities != [None]:
        filtered_df = filtered_df[filtered_df['CITY_NAME'].isin(selected_cities)]

    if filtered_df.empty:
        return [], []
    else:
        routes = sorted(
            [str(r).strip() for r in filtered_df['ROUTE_NAME'].unique() if pd.notna(r)]
        )
        options = [{'label': i, 'value': i} for i in routes]
        return options, []

# Main callback to update all components and the new passenger type chart
@app.callback(
    [Output('cards-container', 'children'),
     Output('pie-chart-transaction-type', 'figure'),
     Output('temporal-chart-ridership', 'figure'),
     Output('passenger-type-chart', 'figure')],
    [Input('depot-dropdown', 'value'),
     Input('city-dropdown', 'value'),
     Input('route-dropdown', 'value')]
)
def update_dashboard(selected_depots, selected_cities, selected_routes):
    filtered_df = df.copy()

    if selected_depots and selected_depots != [None]:
        filtered_df = filtered_df[filtered_df['DEPOT_NAME'].isin(selected_depots)]
    if selected_cities and selected_cities != [None]:
        filtered_df = filtered_df[filtered_df['CITY_NAME'].isin(selected_cities)]
    if selected_routes and selected_routes != [None]:
        filtered_df = filtered_df[filtered_df['ROUTE_NAME'].isin(selected_routes)]
    
    # 1. Cards for Revenue, Ridership, and Peak/Off-Peak Hours
    total_ridership = filtered_df['PASSENGER_COUNT'].sum()
    total_revenue = filtered_df['FARE_COLLECTED'].sum()

    peak_hour = 'N/A'
    off_peak_hour = 'N/A'
    if not filtered_df.empty:
        temporal_ridership_summary = filtered_df.groupby('Time_Interval_Label')['PASSENGER_COUNT'].sum().reset_index()
        if not temporal_ridership_summary.empty:
            peak_hour = temporal_ridership_summary.loc[temporal_ridership_summary['PASSENGER_COUNT'].idxmax()]['Time_Interval_Label']
            off_peak_hour = temporal_ridership_summary.loc[temporal_ridership_summary['PASSENGER_COUNT'].idxmin()]['Time_Interval_Label']

    card_base_class = "rounded-xl shadow-md p-6 text-center transition-transform hover:scale-105"

    cards = [
        html.Div([
            html.Div("👥", className="text-4xl mb-2"),
            html.H3("Total Ridership", className="text-sm md:text-md text-white font-semibold"),
            html.P(f"{total_ridership:,}", className="text-xl md:text-3xl font-bold text-white mt-2")
        ], className=f"bg-gradient-to-r from-blue-500 to-blue-700 {card_base_class}"),

        html.Div([
            html.Div("💰", className="text-4xl mb-2"),
            html.H3("Total Revenue", className="text-sm md:text-md text-white font-semibold"),
            html.P(f"₹ {total_revenue:,}", className="text-xl md:text-3xl font-bold text-white mt-2")
        ], className=f"bg-gradient-to-r from-green-500 to-green-700 {card_base_class}"),

        html.Div([
            html.Div("📈", className="text-4xl mb-2"),
            html.H3("Peak Hour", className="text-sm md:text-md text-white font-semibold"),
            html.P(peak_hour, className="text-xl md:text-3xl font-bold text-white mt-2")
        ], className=f"bg-gradient-to-r from-red-500 to-red-700 {card_base_class}"),

        html.Div([
            html.Div("📉", className="text-4xl mb-2"),
            html.H3("Off-Peak Hour", className="text-sm md:text-md text-white font-semibold"),
            html.P(off_peak_hour, className="text-xl md:text-3xl font-bold text-white mt-2")
        ], className=f"bg-gradient-to-r from-yellow-500 to-yellow-700 {card_base_class}")
    ]

    # 2. Transaction Type Pie Chart
    transaction_type_counts = filtered_df['PAYMENT_MODE'].value_counts().reset_index()
    transaction_type_counts.columns = ['PAYMENT_MODE', 'Count']
    pie_chart = px.pie(transaction_type_counts, values='Count', names='PAYMENT_MODE',
                       title='Transaction Type Distribution', color_discrete_sequence=px.colors.qualitative.Vivid)

    # 3. Temporal Variation Chart (Ridership)
    temporal_ridership = filtered_df.groupby('Time_Interval_Label', sort=False)['PASSENGER_COUNT'].sum().reset_index()
    temporal_ridership_sorted = temporal_ridership.sort_values('Time_Interval_Label', ascending=True)
    temporal_chart = px.bar(temporal_ridership_sorted, x='Time_Interval_Label', y='PASSENGER_COUNT',
                           title='Ridership by 3-Hour Interval', color_discrete_sequence=px.colors.qualitative.Bold)
    temporal_chart.update_xaxes(title_text="Time Interval")
    temporal_chart.update_yaxes(title_text="Total Ridership")

    # 4. New Passenger Type Percentage Chart
    passenger_type_chart = {}
    if 'Passenger Type' in filtered_df.columns:
        passenger_type_counts = filtered_df['Passenger Type'].value_counts(normalize=True).reset_index()
        passenger_type_counts.columns = ['Passenger Type', 'Percentage']
        passenger_type_chart = px.pie(passenger_type_counts, values='Percentage', names='Passenger Type',
                                      title='Passenger Type Distribution', color_discrete_sequence=px.colors.qualitative.Pastel)

    return cards,temporal_chart, pie_chart,passenger_type_chart

# Callback for the ridership area chart based on time range slider
@app.callback(
    Output('ridership-area-chart', 'figure'),
    [Input('depot-dropdown', 'value'),
     Input('city-dropdown', 'value'),
     Input('route-dropdown', 'value'),
     Input('time-range-slider', 'value')]
)
def update_area_chart(selected_depots, selected_cities, selected_routes, time_range):
    filtered_df = df.copy()

    if selected_depots and selected_depots != [None]:
        filtered_df = filtered_df[filtered_df['DEPOT_NAME'].isin(selected_depots)]
    if selected_cities and selected_cities != [None]:
        filtered_df = filtered_df[filtered_df['CITY_NAME'].isin(selected_cities)]
    if selected_routes and selected_routes != [None]:
        filtered_df = filtered_df[filtered_df['ROUTE_NAME'].isin(selected_routes)]

    start_hour, end_hour = time_range
    filtered_df = filtered_df[(filtered_df['Hour'] >= start_hour) & (filtered_df['Hour'] < end_hour)]

    ridership_by_hour = filtered_df.groupby('Hour')['PASSENGER_COUNT'].sum().reset_index()

    area_chart = px.area(ridership_by_hour, x='Hour', y='PASSENGER_COUNT',
                         title=f'Ridership Distribution from {start_hour}:00 to {end_hour}:00',
                         color_discrete_sequence=px.colors.qualitative.D3)
    area_chart.update_xaxes(title_text="Hour of Day", range=[start_hour, end_hour])
    area_chart.update_yaxes(title_text="Total Ridership")

    return area_chart

if __name__ == '__main__':
    app.run(debug=True)