var boxPlotOrdinal = function() {
	let width = 600;
	let height = 600;
	let n = width / 40;
	let tooltipWidth = 300;
	let tooltipOffset = 10;
	let tooltipCircleHtml = function(d) {
		return `
		<div id="tooltip_heading">
			<p class='tooltip-title'><b>${d.x}</b></p>
			<p class='tooltip-data'>${num_format(d.y)}</p>
		</div>
		`;
	}
	let tooltipBoxHtml = function(d){
		return `
			<div id="tooltip_heading">
				<p class='tooltip-title'><b>${d.x1}</b></p>
				<p class='tooltip-data'>Min: ${num_format(d.range[0])}</p>
				<p class='tooltip-data'>Max: ${num_format(d.range[1])}</p>
				<p class='tooltip-data'>Median: ${num_format(d.quartiles[1])}</p>
			</div>
		`;	
	}

	let margin = ({top: 20, right: 20, bottom: 30, left: 40});

	let chartId = "#chart";
	let data = [];

	let num_format = d3.format(",");



	const tooltipPosX = function(pageX) {
		const max_x = width - margin.left - tooltipWidth
		return pageX > max_x - tooltipOffset ? 
			max_x + tooltipOffset : 
			pageX + tooltipOffset
	};

	const tooltipPosY = function(pageY) {
		return pageY + tooltipOffset
	};


	let chart = function(selection) {
		data = selection.datum();
		chartId=selection.node().id;

	  	const svg = selection.append('svg')
							.attr('height', height)
							.attr('width', width);

		// tooltip invoked on mouseover
		const tooltip = d3.select("body")
			.append("div")
			.attr("id", `#${chartId}_tooltip`)
			.attr("class","tooltip")
			.style("width",tooltipWidth)
		;


		const categories = [...new Set(data.map(row => row.x))];

		let x = d3.scalePoint()
		    .domain(categories)
		    .range([margin.left, width - margin.right])

		let bins = categories.map((category, i)=>{
			bin = data.filter(row => row.x === category);
			bin.sort((a, b) => a.y - b.y);
			const values = bin.map(d => d.y);
			const min = values[0];
			const max = values[values.length - 1];
			const q1 = d3.quantile(values, 0.25);
			const q2 = d3.quantile(values, 0.50);
			const q3 = d3.quantile(values, 0.75);
			const iqr = q3 - q1; // interquartile range
			const r0 = Math.max(min, q1 - iqr * 1.5);
			const r1 = Math.min(max, q3 + iqr * 1.5);
			bin.quartiles = [q1, q2, q3];
			bin.range = [r0, r1];
			bin.outliers = bin.filter(v => v.y < r0 || v.y > r1); // TODO
			bin.x0=category;
			bin.x1=categories[i+1];
			return bin
		});

		// let x = d3.scaleLinear()
		//     .domain([d3.min(bins, d => d.x0), d3.max(bins, d => d.x1)])
		//     .rangeRound([margin.left, width - margin.right])



		let y = d3.scaleLinear()
		    .domain([d3.min(bins, d => d.range[0]), d3.max(bins, d => d.range[1])]).nice()
		    .range([height - margin.bottom, margin.top])


		let xAxis = g => g
		    .attr("transform", `translate(0,${height - margin.bottom})`)
		    .call(d3.axisBottom(x))

		let yAxis = g => g
		    .attr("transform", `translate(${margin.left},0)`)
		    .call(d3.axisLeft(y).ticks(null, "s"))
		    .call(g => g.select(".domain").remove())


		const g = svg.append("g")
			.selectAll("g")
			.data(bins)
			.enter().append("g");

		g.append("path")
		  .attr("stroke", "currentColor")
		  .attr("class","whisker")
		  .attr("d", d => console.log(d)
		  // 	`
		  //   M${x(d.x0)},${y(d.range[1])}
		  //   V${y(d.range[0])}
		  // `
		  );

		g.append("path")
			.attr("fill", "#ddd")
			.attr("class","box")
			.attr("d", d => `
				M${x(d.x0) + 1},${y(d.quartiles[2])}
				H${x(d.x1)}
				V${y(d.quartiles[0])}
				H${x(d.x0) + 1}
				Z
			`)

			.on("mouseover", function(d) { 
				d3.select(this).attr("stroke", "black")
				tooltip.style("visibility", "visible")
				.html(tooltipBoxHtml(d))
			})    
			.on("mousemove", function() {
				tooltip.style("left",tooltipPosX(d3.event.pageX)+"px").style("top", tooltipPosY(d3.event.pageY)+"px")
			})
			.on("mouseout", function() {
				d3.select(this).attr("stroke", "none")
				tooltip.style("visibility", "hidden")
			});

		g.append("path")
		  .attr("stroke", "currentColor")
		  .attr("stroke-width", 2)
		  .attr("class","median")
		  .attr("d", d => `
		    M${x(d.x0) + 1},${y(d.quartiles[1])}
		    H${x(d.x1)}
		  `);

		g.append("g")
			.attr("fill", "currentColor")
			.attr("fill-opacity", 0.2)
			.attr("stroke", "none")
			.attr("transform", d => `translate(${x(d.x0)},0)`)
		.selectAll("circle")
		.data(d => d.outliers)
		.enter().append("circle")
			.attr("r", 2)
			.attr("cx", () => (Math.random() - 0.5) * 4)
			.attr("cy", d => y(d.y))
			.attr("class", "outlier")

			.on("mouseover", function(d) { 
				d3.select(this).attr("stroke", "black")
				tooltip.style("visibility", "visible")
				.html(tooltipCircleHtml(d))
			})    
			.on("mousemove", function() {
				tooltip.style("left",tooltipPosX(d3.event.pageX)+"px").style("top", tooltipPosY(d3.event.pageY)+"px")
			})
			.on("mouseout", function() {
				d3.select(this).attr("stroke", "none")
				tooltip.style("visibility", "hidden")
			})

		svg.append("g")
		  .call(xAxis);

		svg.append("g")
		  .call(yAxis);

		return svg;
	}

    chart.chartId = function(value) {
        if (!arguments.length) { return chartId; }
        chartId = value;
        return chart;
    }

    chart.data = function(value) {
        if (!arguments.length) { return data; }
        data = value;
        return chart;
    }

    chart.width = function(value) {
        if (!arguments.length) { return width; }
        width = value;
        return chart;
    }
    chart.height = function(value) {
        if (!arguments.length) { return height; }
        height = value;
        return chart;
    }
    chart.n = function(value) {
        if (!arguments.length) { return n; }
        n = value;
        return chart;
    }
    chart.margin = function(value) {
        if (!arguments.length) { return margin; }
        margin = value;
        return chart;
    }
    chart.tooltipCircleHtml = function(value) {
        if (!arguments.length) { return tooltipCircleHtml; }
        tooltipCircleHtml = value;
        return chart;
    }
    chart.tooltipBoxHtml = function(value) {
        if (!arguments.length) { return tooltipBoxHtml; }
        tooltipBoxHtml = value;
        return chart;
    }
    chart.num_format = num_format;

    return chart;


}