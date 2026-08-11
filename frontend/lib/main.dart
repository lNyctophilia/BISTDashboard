import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const BistDashboardApp());
}

class BistDashboardApp extends StatelessWidget {
  const BistDashboardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BIST Dashboard',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0A0A0C),
        colorScheme: const ColorScheme.dark(
          primary: Colors.blueAccent,
          surface: Color(0xFF151518),
        ),
        useMaterial3: true,
      ),
      home: HomeScreen(),
    );
  }
}
