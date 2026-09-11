(function () {
  var style = getComputedStyle(document.documentElement);
  var accent2 = style.getPropertyValue("--accent2").trim();
  var ink = style.getPropertyValue("--ink").trim();
  var muted = style.getPropertyValue("--muted").trim();
  var rule = style.getPropertyValue("--rule").trim();

  var cats = ["SSP245\n2041–2060", "SSP245\n2081–2100", "SSP585\n2041–2060", "SSP585\n2081–2100"];

  function baseAxis() {
    return {
      type: "category",
      data: cats,
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false },
      axisLabel: { color: muted, fontSize: 12, lineHeight: 16 }
    };
  }

  function bars(watershed) {
    var pos = function (p) { return p.value >= 0 ? "top" : "bottom"; };
    var sign = function (v) { return (v >= 0 ? "+" : "") + v; };
    return [
      {
        name: "流域 30m",
        type: "bar",
        data: watershed,
        barWidth: "38%",
        itemStyle: { color: accent2, borderRadius: [3, 3, 0, 0] },
        label: { show: true, position: pos, color: ink, fontWeight: 700, fontSize: 11,
                 formatter: function (p) { return sign(p.value); } }
      }
    ];
  }

  var chartTas = echarts.init(document.getElementById("chart-tas"), null, { renderer: "svg" });
  chartTas.setOption({
    animation: false,
    grid: { left: 48, right: 24, top: 36, bottom: 44 },
    tooltip: { trigger: "axis", appendToBody: true, valueFormatter: function (v) { return v + " K"; } },
    xAxis: baseAxis(),
    yAxis: {
      type: "value",
      name: "K",
      nameTextStyle: { color: muted },
      axisLabel: { color: muted },
      splitLine: { lineStyle: { color: rule } }
    },
    series: bars([1.43, 2.22, 1.98, 4.32])
  });

  var chartPr = echarts.init(document.getElementById("chart-pr"), null, { renderer: "svg" });
  chartPr.setOption({
    animation: false,
    grid: { left: 52, right: 24, top: 36, bottom: 44 },
    tooltip: { trigger: "axis", appendToBody: true, valueFormatter: function (v) { return v + " %"; } },
    xAxis: baseAxis(),
    yAxis: {
      type: "value",
      name: "%",
      nameTextStyle: { color: muted },
      axisLabel: { color: muted },
      splitLine: { lineStyle: { color: rule } }
    },
    series: bars([1.87, 3.39, -1.5, 6.0])
  });

  window.addEventListener("resize", function () {
    chartTas.resize();
    chartPr.resize();
  });
})();
