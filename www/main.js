

let boxPlot1 = boxPlot().width(600).height(400).n(5);
boxPlot1.tooltipCircleHtml(function(d) {
	return `
	<div id="tooltip_heading">
		<p class='tooltip-title'>Carat: <b>${d.x}</b></p>
		<p class='tooltip-data'>Price: ${boxPlot1.num_format(d.y)}</p>
	</div>
	`;
});


d3.dsv(",", "diamonds.csv", (r) => {
	r.x = +r.carat;
	r.y = +r.price;
	return r;
}).then(data => {
	d3.select("#boxplot1").datum(data).call(boxPlot1);
});






let boxPlot2 = boxPlotOrdinal().width(1000).height(400).n(5);
boxPlot2.tooltipCircleHtml(function(d) {
	return `
	<div id="tooltip_heading">
		<p class='tooltip-title'>Carat: <b>${d.x}</b></p>
		<p class='tooltip-data'>Price: ${boxPlot2.num_format(d.y)}</p>
	</div>
	`;
});


d3.dsv(";", "../results_final.csv", (r) => {
	return {
			x: r.organ, 
			y: +r.DaleChall_min_age
	};
}).then(data => {
	d3.select("#boxplot2").datum(data).call(boxPlot2);
});


