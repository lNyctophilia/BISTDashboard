import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';
import '../widgets/native_chart_widget.dart';

class DetailScreen extends StatefulWidget {
  final String symbol;
  final Map<String, dynamic>? initialQuote;
  
  const DetailScreen({Key? key, required this.symbol, this.initialQuote}) : super(key: key);

  @override
  _DetailScreenState createState() => _DetailScreenState();
}

class _DetailScreenState extends State<DetailScreen> {
  bool _isLoading = true;
  Map<String, dynamic>? _quote;
  Map<String, dynamic>? _signals;
  Map<String, dynamic>? _news;
  Map<String, dynamic>? _kapReports;
  Map<String, dynamic>? _brokerTargets;
  int _kapVisibleWeeks = 1;
  int _newsVisibleWeeks = 1;
  
  List<ChartData>? _chartData;
  String _selectedInterval = '1d';
  bool _isChartLoading = false;

  @override
  void initState() {
    super.initState();
    _quote = widget.initialQuote;
    _fetchData();
  }

  List<ChartData> _parseChartData(Map<String, dynamic>? res) {
    if (res != null && res['data'] != null) {
      final List<dynamic> rawData = res['data'];
      return rawData.map((e) => ChartData(
        time: DateTime.fromMillisecondsSinceEpoch((e['time'] as num).toInt()),
        open: (e['open'] as num).toDouble(),
        high: (e['high'] as num).toDouble(),
        low: (e['low'] as num).toDouble(),
        close: (e['close'] as num).toDouble(),
        volume: (e['volume'] as num).toDouble(),
        ema: e['ema'] != null ? (e['ema'] as num).toDouble() : null,
        sma50: e['sma_50'] != null ? (e['sma_50'] as num).toDouble() : null,
        volumeMa: e['volume_ma'] != null ? (e['volume_ma'] as num).toDouble() : null,
        bollingerUpper: e['bollinger_upper'] != null ? (e['bollinger_upper'] as num).toDouble() : null,
        bollingerMiddle: e['bollinger_middle'] != null ? (e['bollinger_middle'] as num).toDouble() : null,
        bollingerLower: e['bollinger_lower'] != null ? (e['bollinger_lower'] as num).toDouble() : null,
        rsi: e['rsi'] != null ? (e['rsi'] as num).toDouble() : null,
        macd: e['macd'] != null ? (e['macd'] as num).toDouble() : null,
        macdSignal: e['macd_signal'] != null ? (e['macd_signal'] as num).toDouble() : null,
        macdHist: e['macd_hist'] != null ? (e['macd_hist'] as num).toDouble() : null,
      )).toList();
    }
    return [];
  }

  Future<void> _fetchData() async {
    setState(() => _isLoading = true);
    final results = await Future.wait([
      ApiService.getSignals(widget.symbol),
      ApiService.getNews(widget.symbol),
      ApiService.getKapReports(widget.symbol),
      ApiService.getBrokerTargets(widget.symbol),
      ApiService.getChartData(widget.symbol, interval: _selectedInterval),
      ApiService.getQuote(widget.symbol),
    ]);

    if (mounted) {
      setState(() {
        _signals = results[0];
        _news = results[1];
        _kapReports = results[2];
        _brokerTargets = results[3];
        _kapVisibleWeeks = 1;
        _newsVisibleWeeks = 1;
        if (results[5] != null) {
          _quote = results[5];
        }
        _chartData = _parseChartData(results[4]);
        _isLoading = false;
      });
    }
  }

  Future<void> _onIntervalChanged(String newInterval) async {
    if (_selectedInterval != newInterval) {
      setState(() {
        _selectedInterval = newInterval;
        _isChartLoading = true;
      });

      final result = await ApiService.getChartData(widget.symbol, interval: newInterval);

      if (mounted) {
        setState(() {
          _chartData = _parseChartData(result);
          _isChartLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0C),
      appBar: AppBar(
        titleSpacing: 0,
        backgroundColor: const Color(0xFF151518),
        elevation: 0,
        title: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                widget.symbol,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white),
              ),
              if (_quote != null && _quote!['price'] != null) ...[
                const SizedBox(width: 8),
                Text(
                  '₺${_quote!['price']}',
                  style: const TextStyle(fontSize: 15, color: Colors.white),
                ),
                const SizedBox(width: 6),
                Builder(
                  builder: (context) {
                    final num changePct = _quote!['change_percent'] ?? 0;
                    final bool isPositive = changePct >= 0;
                    final Color color = isPositive ? Colors.greenAccent : Colors.redAccent;
                    final String sign = isPositive ? '+' : '';
                    return Text(
                      '($sign$changePct%)',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: color,
                      ),
                    );
                  },
                ),
              ],
            ],
          ),
        ),
        actions: [
          if (_quote != null && _quote!['name'] != null && (_quote!['name'] as String).isNotEmpty)
            Container(
              alignment: Alignment.centerRight,
              constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.4),
              padding: const EdgeInsets.only(right: 16.0, left: 8.0),
              child: Text(
                _quote!['name'],
                style: const TextStyle(fontSize: 13, color: Colors.white60, fontWeight: FontWeight.w500),
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              ),
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.blueAccent))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Stack(
                    children: [
                      if (_chartData != null && _chartData!.isNotEmpty)
                        NativeChartWidget(
                          symbol: widget.symbol,
                          data: _chartData!,
                          selectedInterval: _selectedInterval,
                          onIntervalChanged: _onIntervalChanged,
                        )
                      else
                        Builder(
                          builder: (context) {
                            final isMobile = MediaQuery.of(context).size.width < 600;
                            return Container(
                              height: isMobile ? 420 : 500,
                              decoration: BoxDecoration(
                                color: const Color(0xFF151518),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: Colors.white10),
                              ),
                              child: const Center(child: Text("Grafik verisi bulunamadı", style: TextStyle(color: Colors.white54))),
                            );
                          },
                        ),
                      if (_isChartLoading)
                        Positioned.fill(
                          child: Container(
                            decoration: BoxDecoration(
                              color: Colors.black45,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Center(
                              child: CircularProgressIndicator(color: Colors.blueAccent),
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  _buildSectionTitle('Teknik Analiz (TradingView)'),
                  _buildSignalsSection(),
                  const SizedBox(height: 24),
                  _buildSectionTitle('Banka / Aracı Kurum Hedefleri'),
                  _buildBrokerTargetsSection(),
                  const SizedBox(height: 24),
                  _buildSectionTitle('KAP Raporları'),
                  _buildKapReportsSection(),
                  const SizedBox(height: 24),
                  _buildSectionTitle('Haberler'),
                  _buildNewsSection(),
                ],
              ),
            ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Text(
        title,
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blueAccent),
      ),
    );
  }



  Widget _buildSignalsSection() {
    if (_signals == null || _signals!['timeframes'] == null) {
      return const Text('Sinyal verisi bulunamadı.', style: TextStyle(color: Colors.white54));
    }
    
    final timeframes = _signals!['timeframes'] as Map<String, dynamic>;
    
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: timeframes.entries.map((entry) {
        final label = entry.key;
        final data = entry.value;
        
        if (data['error'] != null) {
          return const SizedBox.shrink(); // Skip errors
        }
        
        final recommendation = data['summary']['RECOMMENDATION'] ?? 'N/A';
        Color recColor = Colors.grey;
        if (recommendation == 'STRONG_BUY' || recommendation == 'BUY') recColor = Colors.greenAccent;
        if (recommendation == 'STRONG_SELL' || recommendation == 'SELL') recColor = Colors.redAccent;
        
        String displayRec = recommendation
            .replaceAll('STRONG_BUY', 'GÜÇLÜ AL')
            .replaceAll('BUY', 'AL')
            .replaceAll('STRONG_SELL', 'GÜÇLÜ SAT')
            .replaceAll('SELL', 'SAT')
            .replaceAll('NEUTRAL', 'NÖTR');
            
        return Container(
          width: (MediaQuery.of(context).size.width - 40) / 2, // 2 columns
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF151518),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white10),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(color: Colors.white70, fontSize: 14)),
              const SizedBox(height: 4),
              Text(
                displayRec,
                style: TextStyle(color: recColor, fontWeight: FontWeight.bold, fontSize: 15),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildBrokerTargetsSection() {
    if (_brokerTargets == null || _brokerTargets!['targets'] == null) {
      return const Text('Hedef fiyat bulunamadı.', style: TextStyle(color: Colors.white54));
    }
    
    final targets = _brokerTargets!['targets'] as List;
    if (targets.isEmpty) {
      return const Text('Hedef fiyat bulunamadı.', style: TextStyle(color: Colors.white54));
    }

    double total = 0;
    int count = 0;
    for (var t in targets) {
      final price = (t['target_price'] ?? 0).toDouble();
      if (price > 0) {
        total += price;
        count++;
      }
    }
    
    double average = count > 0 ? total / count : 0.0;
    
    List<Widget> children = [];
    if (count > 0) {
      children.add(
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8.0),
          child: Column(
            children: [
              Text(
                'Ortalama Beklenti: ₺${average.toStringAsFixed(2)}',
                style: const TextStyle(
                  color: Colors.greenAccent,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              const Divider(color: Colors.white24, thickness: 1),
              const SizedBox(height: 8),
            ],
          ),
        ),
      );
    }

    children.addAll(targets.map((t) {
      String rawRec = (t['recommendation'] ?? '').toString();
      String recText = rawRec;
      final mpMatch = RegExp(r'Model\s+Portfö?y\s*\((.*?)\)', caseSensitive: false).firstMatch(recText);
      if (mpMatch != null) {
        recText = mpMatch.group(1) ?? recText;
      }
      recText = recText.replaceAll(RegExp(r'Model\s+Portfö?y', caseSensitive: false), '').trim();
      if (recText.isEmpty) recText = 'Al';

      return Card(
        color: const Color(0xFF151518),
        margin: const EdgeInsets.only(bottom: 8),
        child: ListTile(
          title: Text(t['broker'], style: const TextStyle(color: Colors.white)),
          subtitle: Text(t['date'], style: const TextStyle(color: Colors.white54)),
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('₺${t['target_price']}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              Text(recText, style: const TextStyle(color: Colors.blueAccent)),
            ],
          ),
        ),
      );
    }).toList());

    return Column(
      children: children,
    );
  }

  int? _getDaysAgo(String? dateStr) {
    if (dateStr == null || dateStr.isEmpty || dateStr == '-') return null;
    try {
      final str = dateStr.trim();
      final parts = str.split(' ');
      if (parts.isNotEmpty) {
        final dParts = parts[0].split('.');
        if (dParts.length == 3) {
          final day = int.parse(dParts[0]);
          final month = int.parse(dParts[1]);
          final year = int.parse(dParts[2]);
          final pubDate = DateTime(year, month, day);
          final now = DateTime.now();
          final today = DateTime(now.year, now.month, now.day);
          int diff = today.difference(pubDate).inDays;
          return diff < 0 ? 0 : diff;
        }
      }
      final parsedIso = DateTime.tryParse(str);
      if (parsedIso != null) {
        final now = DateTime.now();
        final today = DateTime(now.year, now.month, now.day);
        final pubDate = DateTime(parsedIso.year, parsedIso.month, parsedIso.day);
        int diff = today.difference(pubDate).inDays;
        return diff < 0 ? 0 : diff;
      }
    } catch (_) {}
    return null;
  }

  Widget _buildKapReportsSection() {
    if (_kapReports == null || _kapReports!['reports'] == null) {
      return const Text('KAP verisi bulunamadı.', style: TextStyle(color: Colors.white54));
    }
    
    final reports = _kapReports!['reports'] as List;
    if (reports.isEmpty) {
      return const Text('KAP verisi bulunamadı.', style: TextStyle(color: Colors.white54));
    }

    final bool isInfoOnly = reports.length == 1 && reports[0]['category'] == 'Bilgi';

    final displayedReports = reports.where((r) {
      if (isInfoOnly) return true;
      final daysAgo = _getDaysAgo(r['date']?.toString());
      if (daysAgo != null) {
        return daysAgo <= (_kapVisibleWeeks * 7);
      }
      return true;
    }).toList();

    final bool hasMore = !isInfoOnly && displayedReports.length < reports.length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (displayedReports.isEmpty && !isInfoOnly)
          Container(
            padding: const EdgeInsets.all(14),
            margin: const EdgeInsets.only(bottom: 10),
            decoration: BoxDecoration(
              color: const Color(0xFF1E1E24),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.white12),
            ),
            child: Text(
              'Son $_kapVisibleWeeks hafta (${_kapVisibleWeeks * 7} gün) içerisinde KAP bildirimi bulunmamaktadır.',
              style: const TextStyle(color: Colors.white54, fontSize: 13),
              textAlign: TextAlign.center,
            ),
          ),
        ...displayedReports.map((r) {
          final category = r['category'] ?? 'KAP Bildirimi';
          return Card(
            color: const Color(0xFF151518),
            margin: const EdgeInsets.only(bottom: 10),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
              side: const BorderSide(color: Colors.white12, width: 1),
            ),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF24242A),
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: Colors.white24, width: 1),
                                  ),
                                  child: Text(
                                    category,
                                    style: const TextStyle(
                                      color: Colors.white70,
                                      fontSize: 11,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ),
                                Text(
                                  r['date'] ?? '',
                                  style: const TextStyle(color: Colors.white38, fontSize: 11),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              r['title'] ?? '',
                              style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      InkWell(
                        onTap: () async {
                          final url = Uri.parse(r['link'] ?? r['url'] ?? '');
                          if (await canLaunchUrl(url)) {
                            await launchUrl(url);
                          }
                        },
                        borderRadius: BorderRadius.circular(6),
                        child: Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: const Color(0xFF222228),
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(color: Colors.white12, width: 1),
                          ),
                          child: const Icon(Icons.open_in_new, color: Colors.white70, size: 18),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          );
        }),
        if (hasMore) ...[
          const SizedBox(height: 4),
          Center(
            child: InkWell(
              onTap: () {
                setState(() {
                  _kapVisibleWeeks++;
                });
              },
              borderRadius: BorderRadius.circular(20),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                decoration: BoxDecoration(
                  color: const Color(0xFF222228),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: Colors.white24,
                    width: 1,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: const [
                    Text(
                      'Daha Fazla Göster (+1 Hafta)',
                      style: TextStyle(
                        color: Colors.white70,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                    SizedBox(width: 6),
                    Icon(
                      Icons.expand_more,
                      color: Colors.white70,
                      size: 18,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ],
    );
  }
  
  Widget _buildNewsSection() {
    if (_news == null || _news!['news'] == null) {
      return const Text('Haber bulunamadı.', style: TextStyle(color: Colors.white54));
    }
    
    final newsList = _news!['news'] as List;
    if (newsList.isEmpty) {
      return const Text('Haber bulunamadı.', style: TextStyle(color: Colors.white54));
    }

    final bool isInfoOnly = newsList.length == 1 && (newsList[0]['source'] == 'Sistem' || newsList[0]['title'].toString().contains('bulunamadı'));

    final displayedNews = newsList.where((n) {
      if (isInfoOnly) return true;
      final daysAgo = _getDaysAgo(n['date']?.toString());
      if (daysAgo != null) {
        return daysAgo <= (_newsVisibleWeeks * 7);
      }
      return true;
    }).toList();

    final bool hasMore = !isInfoOnly && displayedNews.length < newsList.length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (displayedNews.isEmpty && !isInfoOnly)
          Container(
            padding: const EdgeInsets.all(14),
            margin: const EdgeInsets.only(bottom: 10),
            decoration: BoxDecoration(
              color: const Color(0xFF1E1E24),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.white12),
            ),
            child: Text(
              'Son $_newsVisibleWeeks hafta (${_newsVisibleWeeks * 7} gün) içerisinde haber bulunmamaktadır.',
              style: const TextStyle(color: Colors.white54, fontSize: 13),
              textAlign: TextAlign.center,
            ),
          ),
        ...displayedNews.map((n) {
          final String dateStr = n['date'] != null && n['date'].toString() != '-' ? n['date'].toString() : '';
          final String subtitleText = dateStr.isNotEmpty ? '${n['source']} • $dateStr' : (n['source'] ?? '');

          return Card(
            color: const Color(0xFF151518),
            margin: const EdgeInsets.only(bottom: 8),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
              side: const BorderSide(color: Colors.white12, width: 1),
            ),
            child: ListTile(
              title: Text(n['title'] ?? '', style: const TextStyle(color: Colors.white, fontSize: 14)),
              subtitle: subtitleText.isNotEmpty ? Text(subtitleText, style: const TextStyle(color: Colors.white54, fontSize: 12)) : null,
              trailing: const Icon(Icons.open_in_new, color: Colors.white70, size: 18),
              onTap: () async {
                final urlStr = n['url'] ?? n['link'] ?? '';
                if (urlStr.isNotEmpty && urlStr != '#') {
                  final url = Uri.parse(urlStr);
                  if (await canLaunchUrl(url)) {
                    await launchUrl(url);
                  }
                }
              },
            ),
          );
        }),
        if (hasMore) ...[
          const SizedBox(height: 4),
          Center(
            child: InkWell(
              onTap: () {
                setState(() {
                  _newsVisibleWeeks++;
                });
              },
              borderRadius: BorderRadius.circular(20),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                decoration: BoxDecoration(
                  color: const Color(0xFF222228),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: Colors.white24,
                    width: 1,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: const [
                    Text(
                      'Daha Fazla Göster (+1 Hafta)',
                      style: TextStyle(
                        color: Colors.white70,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                    SizedBox(width: 6),
                    Icon(
                      Icons.expand_more,
                      color: Colors.white70,
                      size: 18,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ],
    );
  }
}
