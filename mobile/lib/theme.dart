import 'package:flutter/material.dart';

/// Warm, trustworthy, government-grade palette with delight — mirrors the web app.
class C {
  static const ink = Color(0xFF1A1714);
  static const inkSoft = Color(0xFF4A453E);
  static const inkFaint = Color(0xFF8A8378);
  static const paper = Color(0xFFFBF7F0);
  static const card = Color(0xFFFFFFFF);
  static const sunk = Color(0xFFF2EBDF);
  static const saffron = Color(0xFFE8730C);
  static const saffronDeep = Color(0xFFC25A00);
  static const saffronSoft = Color(0xFFFDEBD8);
  static const leaf = Color(0xFF1B873F);
  static const leafSoft = Color(0xFFE3F3E8);
  static const amber = Color(0xFFB26A00);
  static const amberSoft = Color(0xFFFBEFD6);
  static const flag = Color(0xFFC62828);
  static const flagSoft = Color(0xFFFBE3E3);
  static const indigo = Color(0xFF2A3B8F);
}

Color tierColor(String tier) => switch (tier) {
      "green" => C.leaf,
      "amber" => C.amber,
      "red" => C.flag,
      _ => C.amber,
    };

ThemeData sahayakTheme() {
  final base = ThemeData(useMaterial3: true, brightness: Brightness.light);
  return base.copyWith(
    scaffoldBackgroundColor: C.paper,
    colorScheme: base.colorScheme.copyWith(
      primary: C.saffron,
      secondary: C.indigo,
      surface: C.card,
    ),
    textTheme: base.textTheme.apply(bodyColor: C.ink, displayColor: C.ink),
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.transparent,
      elevation: 0,
      foregroundColor: C.ink,
      centerTitle: false,
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: C.saffron,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
      ),
    ),
  );
}
