import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Can be set via flutter build --dart-define=API_URL=https://your-render-url.onrender.com/api
  static const String _envUrl = String.fromEnvironment('API_URL');
  // Canlı Render URL adresi
  static const String _defaultUrl = 'https://bistdashboard-9pag.onrender.com/api';

  static String get baseUrl => _envUrl.isNotEmpty ? _envUrl : _defaultUrl;

  static Future<Map<String, dynamic>?> getQuote(String symbol) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/quote/$symbol'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return null;
    } catch (e) {
      print('Error fetching quote: $e');
      return null;
    }
  }

  static Future<Map<String, Map<String, dynamic>>?> getBatchQuotes(List<String> symbols) async {
    if (symbols.isEmpty) return {};
    try {
      final joined = symbols.join(',');
      final response = await http.get(Uri.parse('$baseUrl/quotes/batch?symbols=$joined'));
      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final Map<String, Map<String, dynamic>> result = {};
        data.forEach((key, value) {
          if (value is Map<String, dynamic>) {
            result[key] = value;
          }
        });
        return result;
      }
      return null;
    } catch (e) {
      print('Error fetching batch quotes: $e');
      return null;
    }
  }

  static Future<Map<String, dynamic>?> getSignals(String symbol) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/signals/$symbol'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return null;
    } catch (e) {
      print('Error fetching signals: $e');
      return null;
    }
  }
  
  static Future<Map<String, dynamic>?> getNews(String symbol) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/news/$symbol'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return null;
    } catch (e) {
      print('Error fetching news: $e');
      return null;
    }
  }

  static Future<Map<String, dynamic>?> getKapReports(String symbol) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/kap/$symbol'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return null;
    } catch (e) {
      print('Error fetching KAP: $e');
      return null;
    }
  }

  static Future<Map<String, dynamic>?> getBrokerTargets(String symbol) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/broker-targets/$symbol'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return null;
    } catch (e) {
      print('Error fetching broker targets: $e');
      return null;
    }
  }
  static Future<Map<String, dynamic>?> getChartData(String symbol, {String interval = "1d"}) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/chart/$symbol?interval=$interval'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return null;
    } catch (e) {
      print('Error fetching chart data: $e');
      return null;
    }
  }
}
