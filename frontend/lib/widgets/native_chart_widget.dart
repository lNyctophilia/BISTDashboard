// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:ui_web' as ui_web;
import 'dart:convert';
import 'dart:async';
import 'package:flutter/material.dart';

class ChartData {
  ChartData({
    required this.time,
    required this.open,
    required this.high,
    required this.low,
    required this.close,
    required this.volume,
    this.ema,
    this.sma50,
    this.volumeMa,
    this.bollingerUpper,
    this.bollingerMiddle,
    this.bollingerLower,
    this.rsi,
    this.macd,
    this.macdSignal,
    this.macdHist,
  });

  final DateTime time;
  final double open;
  final double high;
  final double low;
  final double close;
  final double volume;
  final double? ema;
  final double? sma50;
  final double? volumeMa;
  final double? bollingerUpper;
  final double? bollingerMiddle;
  final double? bollingerLower;
  final double? rsi;
  final double? macd;
  final double? macdSignal;
  final double? macdHist;
}

class NativeChartWidget extends StatefulWidget {
  final String symbol;
  final List<ChartData> data;
  final String selectedInterval;
  final Function(String)? onIntervalChanged;

  const NativeChartWidget({
    super.key,
    required this.symbol,
    required this.data,
    this.selectedInterval = '1d',
    this.onIntervalChanged,
  });

  @override
  State<NativeChartWidget> createState() => _NativeChartWidgetState();
}

class _NativeChartWidgetState extends State<NativeChartWidget> {
  late String _viewType;
  StreamSubscription? _msgSub;

  @override
  void initState() {
    super.initState();
    _registerView();
    _listenToMessages();
  }

  @override
  void didUpdateWidget(covariant NativeChartWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.symbol != widget.symbol ||
        oldWidget.data != widget.data ||
        oldWidget.selectedInterval != widget.selectedInterval) {
      _registerView();
    }
  }

  @override
  void dispose() {
    _msgSub?.cancel();
    super.dispose();
  }

  void _listenToMessages() {
    _msgSub?.cancel();
    _msgSub = html.window.onMessage.listen((event) {
      try {
        final raw = event.data.toString();
        final data = jsonDecode(raw);
        if (data != null && data['type'] == 'INTERVAL_CHANGED') {
          final newInterval = data['interval'].toString();
          if (widget.onIntervalChanged != null) {
            widget.onIntervalChanged!(newInterval);
          }
        }
      } catch (_) {}
    });
  }

  void _registerView() {
    _viewType = 'tv-lw-chart-${widget.symbol}-${DateTime.now().microsecondsSinceEpoch}';

    final jsonList = widget.data.map((e) => {
      'time': e.time.millisecondsSinceEpoch,
      'open': e.open,
      'high': e.high,
      'low': e.low,
      'close': e.close,
      'volume': e.volume,
      'ema': e.ema,
      'sma_50': e.sma50,
      'volume_ma': e.volumeMa,
      'bollinger_upper': e.bollingerUpper,
      'bollinger_middle': e.bollingerMiddle,
      'bollinger_lower': e.bollingerLower,
      'rsi': e.rsi,
      'macd': e.macd,
      'macd_signal': e.macdSignal,
      'macd_hist': e.macdHist,
    }).toList();

    final jsonString = jsonEncode(jsonList);
    final cleanSymbol = widget.symbol.replaceAll('.IS', '').replaceAll('BIST:', '').trim().toUpperCase();
    final currentInterval = widget.selectedInterval;

    final sel1h = currentInterval == '1h' ? 'selected' : '';
    final sel4h = currentInterval == '4h' ? 'selected' : '';
    final sel1d = currentInterval == '1d' ? 'selected' : '';
    final sel1wk = currentInterval == '1wk' ? 'selected' : '';
    final sel1mo = currentInterval == '1mo' ? 'selected' : '';

    final chartHtml = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
    body {
      background-color: #131722;
      color: #D1D4DC;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      overflow: hidden;
      height: 100vh;
      width: 100vw;
      display: flex;
    }
    
    /* Left Vertical Toolbar */
    .sidebar {
      width: 52px;
      background-color: #1E222D;
      border-right: 1px solid #2A2E39;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 8px 4px;
      gap: 6px;
      z-index: 20;
    }
    .tb-btn {
      width: 44px;
      height: 32px;
      background: #2A2E39;
      border: 1px solid #363C4E;
      border-radius: 6px;
      color: #90A4AE;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
    }
    .tb-btn:hover {
      background: #363C4E;
      color: #FFFFFF;
    }
    .tb-btn.active {
      background: #2962FF;
      border-color: #2962FF;
      color: #FFFFFF;
      box-shadow: 0 0 8px rgba(41, 98, 255, 0.4);
    }
    .tb-btn.auto-btn {
      margin-top: auto;
      background: rgba(41, 98, 255, 0.15);
      border-color: rgba(41, 98, 255, 0.3);
      color: #2962FF;
      font-size: 11px;
    }
    .tb-btn.auto-btn.active {
      background: #2962FF;
      border-color: #2962FF;
      color: #FFFFFF;
      box-shadow: 0 0 8px rgba(41, 98, 255, 0.4);
    }
    .tb-btn.reset-btn {
      background: rgba(38, 166, 154, 0.15);
      border-color: rgba(38, 166, 154, 0.3);
      color: #26a69a;
      font-size: 14px;
    }
    .tb-btn.reset-btn:hover {
      background: #26a69a;
      color: #ffffff;
    }

    /* Main Chart Area */
    .chart-container {
      flex: 1;
      position: relative;
      height: 100%;
      overflow: hidden;
    }
    #tv-chart {
      width: 100%;
      height: 100%;
    }

    /* Legend Overlay */
    .legend-overlay {
      position: absolute;
      top: 8px;
      left: 12px;
      z-index: 10;
      font-size: 12px;
      line-height: 1.5;
      font-family: monospace;
      pointer-events: none;
      background: rgba(19, 23, 34, 0.85);
      padding: 4px 8px;
      border-radius: 4px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(4px);
    }
    .legend-title { font-weight: bold; color: #3B82F6; font-size: 13px; margin-right: 8px; }
    .val-up { color: #089981; font-weight: bold; }
    .val-down { color: #F23645; font-weight: bold; }
    .val-indicator { margin-left: 8px; font-weight: 600; }

    /* Top Right Timeframe Dropdown Bar */
    .timeframe-bar {
      position: absolute;
      top: 8px;
      right: 70px;
      z-index: 15;
      display: flex;
      align-items: center;
    }
    .tf-dropdown {
      background: #1E222D;
      color: #D1D4DC;
      border: 1px solid #363C4E;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 700;
      padding: 4px 8px;
      height: 32px;
      cursor: pointer;
      outline: none;
      transition: all 0.15s ease;
      text-align: center;
      width: 64px;
    }
    .tf-dropdown:hover {
      border-color: #2962FF;
      color: #FFFFFF;
    }
  </style>
</head>
<body>
  <div class="sidebar">
    <button class="tb-btn" id="btn-vol" title="Hacim (Volume)">VOL</button>
    <button class="tb-btn" id="btn-ema" title="EMA (20)">EMA</button>
    <button class="tb-btn" id="btn-sma" title="SMA (50)">SMA</button>
    <button class="tb-btn" id="btn-bb" title="Bollinger Bantları">BB</button>
    <button class="tb-btn" id="btn-rsi" title="RSI (14)">RSI</button>
    <button class="tb-btn" id="btn-macd" title="MACD">MACD</button>
    <button class="tb-btn" id="btn-sr" title="Destek ve Direnç Seviyeleri">D/D</button>
    <button class="tb-btn active" id="btn-grid" title="Izgara">GRID</button>
    <button class="tb-btn auto-btn" id="btn-auto" title="Otomatik Fiyat Ölçeği (OTO / Manuel)">OTO</button>
    <button class="tb-btn reset-btn" id="btn-reset" title="Odakla / Sıfırla">🎯</button>
  </div>

  <div class="chart-container">
    <div class="legend-overlay" id="legend"></div>

    <div class="timeframe-bar">
      <select id="tf-select" class="tf-dropdown">
        <option value="1h" $sel1h>1H</option>
        <option value="4h" $sel4h>4H</option>
        <option value="1d" $sel1d>1D</option>
        <option value="1wk" $sel1wk>1W</option>
        <option value="1mo" $sel1mo>1M</option>
      </select>
    </div>

    <div id="tv-chart"></div>
  </div>

  <script>
    const rawData = $jsonString;
    const symbol = "$cleanSymbol";
    const currentInterval = "$currentInterval";

    const container = document.getElementById('tv-chart');
    const legend = document.getElementById('legend');
    const autoBtn = document.getElementById('btn-auto');

    let priceZoomFactor = 1.0;

    const chart = LightweightCharts.createChart(container, {
      layout: {
        background: { type: 'solid', color: '#131722' },
        textColor: '#D1D4DC',
        fontSize: 12,
      },
      grid: {
        vertLines: { color: '#1E222D', style: 1 },
        horzLines: { color: '#1E222D', style: 1 },
      },
      crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
        vertLine: { color: '#758696', width: 1, style: 3, labelBackgroundColor: '#363C4E' },
        horzLine: { color: '#758696', width: 1, style: 3, labelBackgroundColor: '#363C4E' },
      },
      rightPriceScale: {
        borderColor: '#2B2B43',
        visible: true,
        autoScale: false,
        scaleMargins: { top: 0.1, bottom: 0.2 },
      },
      timeScale: {
        borderColor: '#2B2B43',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 8,
        barSpacing: 10,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMove: true,
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
      handleScale: {
        axisPressedMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    // Candlesticks
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#089981',
      downColor: '#F23645',
      wickUpColor: '#089981',
      wickDownColor: '#F23645',
      borderUpColor: '#089981',
      borderDownColor: '#F23645',
      autoscaleInfoProvider: (original) => {
        const res = original();
        if (!res || !res.priceRange) return res;
        if (priceZoomFactor === 1.0) return res;

        const min = res.priceRange.minValue;
        const max = res.priceRange.maxValue;
        if (min === null || max === null || min === undefined || max === undefined || min === max) {
          return res;
        }

        const mid = (min + max) / 2;
        const halfRange = (max - min) / 2;
        const newHalfRange = halfRange / priceZoomFactor;

        return {
          priceRange: {
            minValue: mid - newHalfRange,
            maxValue: mid + newHalfRange,
          },
          margins: res.margins,
        };
      },
    });

    // Volume Histogram
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
      visible: false,
    });
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    // EMA 20
    const emaSeries = chart.addLineSeries({
      color: '#2962FF',
      lineWidth: 2,
      title: 'EMA 20',
      visible: false,
    });

    // SMA 50
    const smaSeries = chart.addLineSeries({
      color: '#FF6D00',
      lineWidth: 2,
      title: 'SMA 50',
      visible: false,
    });

    // Bollinger Bands
    const bbUpperSeries = chart.addLineSeries({
      color: '#E91E63',
      lineWidth: 1,
      lineStyle: 2,
      title: 'BB Üst',
      visible: false,
    });
    const bbMiddleSeries = chart.addLineSeries({
      color: '#2196F3',
      lineWidth: 1,
      lineStyle: 0,
      title: 'BB Orta',
      visible: false,
    });
    const bbLowerSeries = chart.addLineSeries({
      color: '#E91E63',
      lineWidth: 1,
      lineStyle: 2,
      title: 'BB Alt',
      visible: false,
    });

    // RSI 14
    const rsiSeries = chart.addLineSeries({
      color: '#9C27B0',
      lineWidth: 2,
      priceScaleId: 'rsi',
      title: 'RSI 14',
      visible: false,
    });
    chart.priceScale('rsi').applyOptions({
      scaleMargins: { top: 0.75, bottom: 0.05 },
    });

    // MACD
    const macdSeries = chart.addLineSeries({
      color: '#2196F3',
      lineWidth: 2,
      priceScaleId: 'macd',
      title: 'MACD',
      visible: false,
    });
    const macdSignalSeries = chart.addLineSeries({
      color: '#FF9800',
      lineWidth: 1,
      priceScaleId: 'macd',
      title: 'Sinyal',
      visible: false,
    });
    const macdHistSeries = chart.addHistogramSeries({
      priceScaleId: 'macd',
      title: 'MACD Hist',
      visible: false,
    });
    chart.priceScale('macd').applyOptions({
      scaleMargins: { top: 0.75, bottom: 0.05 },
    });

    // Support & Resistance Price Lines array
    const srPriceLines = [];

    function computeAndDrawSR() {
      // Clear existing lines
      srPriceLines.forEach(line => candleSeries.removePriceLine(line));
      srPriceLines.length = 0;

      if (!candles || candles.length === 0) return;

      const recent = candles.slice(-30);
      let rHigh = -Infinity, rLow = Infinity;
      recent.forEach(c => {
        if (c.high > rHigh) rHigh = c.high;
        if (c.low < rLow) rLow = c.low;
      });
      const rClose = recent[recent.length - 1].close;

      const p = Number(((rHigh + rLow + rClose) / 3).toFixed(2));
      const r1 = Number(((2 * p) - rLow).toFixed(2));
      const s1 = Number(((2 * p) - rHigh).toFixed(2));
      const r2 = Number((p + (rHigh - rLow)).toFixed(2));
      const s2 = Number((p - (rHigh - rLow)).toFixed(2));

      srPriceLines.push(candleSeries.createPriceLine({
        price: r2,
        color: '#F23645',
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: 'Direnç 2 (R2)',
      }));

      srPriceLines.push(candleSeries.createPriceLine({
        price: r1,
        color: '#FF5252',
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: 'Direnç 1 (R1)',
      }));

      srPriceLines.push(candleSeries.createPriceLine({
        price: p,
        color: '#FFD600',
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dotted,
        axisLabelVisible: true,
        title: 'Pivot (P)',
      }));

      srPriceLines.push(candleSeries.createPriceLine({
        price: s1,
        color: '#26A69A',
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: 'Destek 1 (S1)',
      }));

      srPriceLines.push(candleSeries.createPriceLine({
        price: s2,
        color: '#089981',
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: 'Destek 2 (S2)',
      }));
    }

    // Sort & Transform Data
    const sortedData = (rawData || []).sort((a, b) => a.time - b.time);
    
    // Deduplicate timestamps if any
    const uniqueMap = new Map();
    sortedData.forEach(d => {
      const tSec = Math.floor(d.time / 1000);
      if (!uniqueMap.has(tSec)) {
        uniqueMap.set(tSec, d);
      }
    });

    const candles = [];
    const volumes = [];
    const emas = [];
    const smas = [];
    const bbUpper = [];
    const bbMiddle = [];
    const bbLower = [];
    const rsis = [];
    const macds = [];
    const macdSignals = [];
    const macdHists = [];

    uniqueMap.forEach((d, tSec) => {
      candles.push({ time: tSec, open: d.open, high: d.high, low: d.low, close: d.close });
      volumes.push({
        time: tSec,
        value: d.volume,
        color: d.close >= d.open ? 'rgba(8, 153, 129, 0.4)' : 'rgba(242, 54, 69, 0.4)'
      });

      if (d.ema !== null && d.ema !== undefined) emas.push({ time: tSec, value: d.ema });
      if (d.sma_50 !== null && d.sma_50 !== undefined) smas.push({ time: tSec, value: d.sma_50 });

      if (d.bollinger_upper !== null && d.bollinger_upper !== undefined) bbUpper.push({ time: tSec, value: d.bollinger_upper });
      if (d.bollinger_middle !== null && d.bollinger_middle !== undefined) bbMiddle.push({ time: tSec, value: d.bollinger_middle });
      if (d.bollinger_lower !== null && d.bollinger_lower !== undefined) bbLower.push({ time: tSec, value: d.bollinger_lower });

      if (d.rsi !== null && d.rsi !== undefined) rsis.push({ time: tSec, value: d.rsi });

      if (d.macd !== null && d.macd !== undefined) macds.push({ time: tSec, value: d.macd });
      if (d.macd_signal !== null && d.macd_signal !== undefined) macdSignals.push({ time: tSec, value: d.macd_signal });
      if (d.macd_hist !== null && d.macd_hist !== undefined) {
        macdHists.push({
          time: tSec,
          value: d.macd_hist,
          color: d.macd_hist >= 0 ? 'rgba(8, 153, 129, 0.7)' : 'rgba(242, 54, 69, 0.7)'
        });
      }
    });

    candleSeries.setData(candles);
    volumeSeries.setData(volumes);
    emaSeries.setData(emas);
    smaSeries.setData(smas);
    bbUpperSeries.setData(bbUpper);
    bbMiddleSeries.setData(bbMiddle);
    bbLowerSeries.setData(bbLower);
    rsiSeries.setData(rsis);
    macdSeries.setData(macds);
    macdSignalSeries.setData(macdSignals);
    macdHistSeries.setData(macdHists);

    chart.timeScale().fitContent();

    // Resize Handling
    const resizeObserver = new ResizeObserver(entries => {
      if (entries[0]) {
        const { width, height } = entries[0].contentRect;
        chart.applyOptions({ width, height });
      }
    });
    resizeObserver.observe(container);

    // Legend
    function updateLegend(param) {
      if (!param.time || !param.seriesData || param.seriesData.size === 0) {
        if (candles.length > 0) {
          const last = candles[candles.length - 1];
          const chg = (((last.close - last.open) / last.open) * 100).toFixed(2);
          const cls = last.close >= last.open ? 'val-up' : 'val-down';
          const sign = chg >= 0 ? '+' : '';
          legend.innerHTML = `<span class="legend-title">\${symbol}</span>` +
            `A: <span class="\${cls}">\${last.open}</span> ` +
            `Y: <span class="\${cls}">\${last.high}</span> ` +
            `D: <span class="\${cls}">\${last.low}</span> ` +
            `K: <span class="\${cls}">\${last.close}</span> ` +
            `(\${sign}\${chg}%)`;
        }
        return;
      }

      const cData = param.seriesData.get(candleSeries);
      if (cData) {
        const chg = (((cData.close - cData.open) / cData.open) * 100).toFixed(2);
        const cls = cData.close >= cData.open ? 'val-up' : 'val-down';
        const sign = chg >= 0 ? '+' : '';
        let txt = `<span class="legend-title">\${symbol}</span>` +
          `A: <span class="\${cls}">\${cData.open}</span> ` +
          `Y: <span class="\${cls}">\${cData.high}</span> ` +
          `D: <span class="\${cls}">\${cData.low}</span> ` +
          `K: <span class="\${cls}">\${cData.close}</span> ` +
          `<span class="\${cls}">(\${sign}\${chg}%)</span>`;

        const emaVal = param.seriesData.get(emaSeries);
        if (emaVal && emaSeries.options().visible) {
          txt += ` <span class="val-indicator" style="color:#2962FF">EMA: \${emaVal.value}</span>`;
        }
        const smaVal = param.seriesData.get(smaSeries);
        if (smaVal && smaSeries.options().visible) {
          txt += ` <span class="val-indicator" style="color:#FF6D00">SMA: \${smaVal.value}</span>`;
        }
        const rsiVal = param.seriesData.get(rsiSeries);
        if (rsiVal && rsiSeries.options().visible) {
          txt += ` <span class="val-indicator" style="color:#9C27B0">RSI: \${rsiVal.value}</span>`;
        }
        legend.innerHTML = txt;
      }
    }
    chart.subscribeCrosshairMove(updateLegend);
    updateLegend({});

    // Toolbar Buttons
    function setupToggle(btnId, action) {
      const btn = document.getElementById(btnId);
      if (!btn) return;
      btn.addEventListener('click', () => {
        const isActive = btn.classList.toggle('active');
        action(isActive);
      });
    }

    setupToggle('btn-vol', active => volumeSeries.applyOptions({ visible: active }));
    setupToggle('btn-ema', active => emaSeries.applyOptions({ visible: active }));
    setupToggle('btn-sma', active => smaSeries.applyOptions({ visible: active }));
    setupToggle('btn-bb', active => {
      bbUpperSeries.applyOptions({ visible: active });
      bbMiddleSeries.applyOptions({ visible: active });
      bbLowerSeries.applyOptions({ visible: active });
    });
    setupToggle('btn-rsi', active => rsiSeries.applyOptions({ visible: active }));
    setupToggle('btn-macd', active => {
      macdSeries.applyOptions({ visible: active });
      macdSignalSeries.applyOptions({ visible: active });
      macdHistSeries.applyOptions({ visible: active });
    });
    setupToggle('btn-sr', active => {
      if (active) {
        computeAndDrawSR();
      } else {
        srPriceLines.forEach(line => candleSeries.removePriceLine(line));
        srPriceLines.length = 0;
      }
    });
    setupToggle('btn-grid', active => {
      chart.applyOptions({
        grid: {
          vertLines: { visible: active },
          horzLines: { visible: active }
        }
      });
    });

    // Timeframe Change Handler
    const tfSelect = document.getElementById('tf-select');
    if (tfSelect) {
      tfSelect.addEventListener('change', (e) => {
        const newTf = e.target.value;
        if (newTf !== currentInterval) {
          window.parent.postMessage(JSON.stringify({ type: 'INTERVAL_CHANGED', interval: newTf }), '*');
        }
      });
    }

    // Auto / Manual Price Scale Toggle
    setupToggle('btn-auto', active => {
      if (active) {
        priceZoomFactor = 1.0;
        chart.priceScale('right').applyOptions({
          autoScale: true,
          scaleMargins: { top: 0.1, bottom: 0.2 }
        });
        candleSeries.applyOptions({});
      } else {
        chart.priceScale('right').applyOptions({
          autoScale: false
        });
      }
    });

    // Reset Button
    document.getElementById('btn-reset').addEventListener('click', () => {
      priceZoomFactor = 1.0;
      chart.priceScale('right').applyOptions({
        autoScale: false,
        scaleMargins: { top: 0.1, bottom: 0.2 }
      });
      if (autoBtn && autoBtn.classList.contains('active')) {
        autoBtn.classList.remove('active');
      }
      candleSeries.applyOptions({});
      chart.timeScale().fitContent();
    });

    // Mousedown listener to detect left-click drag on price scale
    container.addEventListener('mousedown', (e) => {
      const rect = container.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const isRightAxis = mouseX >= (rect.width - 85);

      if (isRightAxis) {
        if (autoBtn && autoBtn.classList.contains('active')) {
          autoBtn.classList.remove('active');
        }
        chart.priceScale('right').applyOptions({ autoScale: false });
      }
    });

    // Vertical (Price Scale) Wheel Interactions (Capture Phase)
    container.addEventListener('wheel', (e) => {
      const rect = container.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const isRightAxis = mouseX >= (rect.width - 85); // Right 85px (Price Axis)

      if (isRightAxis || e.shiftKey) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        const zoomStep = 0.15;
        if (e.deltaY < 0) {
          priceZoomFactor *= (1 + zoomStep);
        } else {
          priceZoomFactor /= (1 + zoomStep);
        }

        // Allow deep vertical zoom (0.001x to 2000x)
        priceZoomFactor = Math.max(0.001, Math.min(2000.0, priceZoomFactor));

        if (autoBtn && autoBtn.classList.contains('active')) {
          if (Math.abs(priceZoomFactor - 1.0) > 0.01) {
            autoBtn.classList.remove('active');
          }
        }

        // Strictly keep autoScale: false so horizontal date scrolling DOES NOT auto-scale!
        chart.priceScale('right').applyOptions({ autoScale: false });
        candleSeries.applyOptions({});
      }
    }, { capture: true, passive: false });
  </script>
</body>
</html>
''';

    final iframe = html.IFrameElement()
      ..width = '100%'
      ..height = '100%'
      ..src = 'data:text/html;charset=utf-8,' + Uri.encodeComponent(chartHtml)
      ..style.border = 'none';

    ui_web.platformViewRegistry.registerViewFactory(
      _viewType,
      (int viewId) => iframe,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 480,
      decoration: BoxDecoration(
        color: const Color(0xFF131722),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: HtmlElementView(viewType: _viewType),
      ),
    );
  }
}
