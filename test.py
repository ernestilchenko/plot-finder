from plot_finder import Plot, PlotAnalyzer, NothingFoundError

plot = Plot(x=460166.4, y=313380.5)
print(plot.centroid)
print(plot.srid)

analyzer = PlotAnalyzer(plot=plot)
places = analyzer.education(radius=4000)
print(places)
