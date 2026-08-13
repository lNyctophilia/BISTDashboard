import 'package:shared_preferences/shared_preferences.dart';
import '../data/bist_stocks.dart';

class StorageService {
  static const String _watchlistKey = 'watchlist_symbols';

  static Future<void> clearCacheExceptWatchlist() async {
    final prefs = await SharedPreferences.getInstance();
    final keys = prefs.getKeys();
    for (String key in keys) {
      if (key != _watchlistKey) {
        await prefs.remove(key);
      }
    }
  }

  static Future<void> clearAllData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_watchlistKey, <String>[]);
    final keys = prefs.getKeys();
    for (String key in keys) {
      if (key != _watchlistKey && key != 'bist_remember_auth' && key != 'bist_auth') {
        await prefs.remove(key);
      }
    }
  }

  static Future<List<String>> getWatchlist() async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_watchlistKey);
    
    if (list == null) {
      // First time launch: return BIST 30
      final defaultList = List<String>.from(BistStocks.bist30);
      await prefs.setStringList(_watchlistKey, defaultList);
      return defaultList;
    }
    
    return List<String>.from(list);
  }

  static Future<void> saveWatchlist(List<String> watchlist) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_watchlistKey, List<String>.from(watchlist));
  }

  static Future<void> resetToDefaultBist30() async {
    final defaultList = List<String>.from(BistStocks.bist30);
    await saveWatchlist(defaultList);
  }

  static Future<void> addSymbol(String symbol) async {
    final list = await getWatchlist();
    if (!list.contains(symbol)) {
      list.add(symbol);
      await saveWatchlist(list);
    }
  }

  static Future<void> removeSymbol(String symbol) async {
    final list = await getWatchlist();
    if (list.contains(symbol)) {
      list.remove(symbol);
      await saveWatchlist(list);
    }
  }
}

