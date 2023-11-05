
import plotly.graph_objs as go

def plot_lateral_loads(seismic_shear_story_plot, seismic_shear_elevation_plot, wind_shear_story_plot, wind_shear_elevation_plot):

    # create traces for seismic and wind data if both are present
    if seismic_shear_story_plot and wind_shear_story_plot:
        seismic_trace = go.Scatter(x=seismic_shear_story_plot, y=seismic_shear_elevation_plot, name='Seismic')
        wind_trace = go.Scatter(x=wind_shear_story_plot, y=wind_shear_elevation_plot, name='Wind')
        data = [seismic_trace, wind_trace]
    elif seismic_shear_story_plot:
        data = [go.Scatter(x=seismic_shear_story_plot, y=seismic_shear_elevation_plot, name='Seismic')]
    elif wind_shear_story_plot:
        data = [go.Scatter(x=wind_shear_story_plot, y=wind_shear_elevation_plot, name='Wind')]

    # create layout for plot
    layout = go.Layout(title='Lateral Loads', xaxis_title='Shear', yaxis_title='Elevation')

    # add traces and layout to figure
    fig = go.Figure(data=data, layout=layout)

    # show figure
    # fig.show()
    return fig
if __name__ == '__main__':
        
    seimsic_shear_story_plot = [312133.33,312133.33,54733.33,54733.33,0]
    seismic_shear_elevation_plot = [24, 24, 12, 12, 0]
    wind_shear_story_plot = [31213.33,31213.33,5473.33,5473.33,0]
    wind_shear_elevation_plot = [24, 24, 12, 12, 0]

    plot_lateral_loads(seimsic_shear_story_plot, seismic_shear_elevation_plot, wind_shear_story_plot, wind_shear_elevation_plot)