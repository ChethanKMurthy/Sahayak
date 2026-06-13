import 'package:flutter/widgets.dart';

/// Shared layout spacing — a single source so screens stay visually consistent.
class Insets {
  Insets._();
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 40;
}

/// Corner radii used across cards, pills and sheets.
class Radii {
  Radii._();
  static const Radius card = Radius.circular(16);
  static const Radius pill = Radius.circular(999);
}

/// Animation durations (kept in one place so motion feels coherent).
class Motion {
  Motion._();
  static const Duration fast = Duration(milliseconds: 150);
  static const Duration base = Duration(milliseconds: 280);
  static const Duration slow = Duration(milliseconds: 600);
}

/// Responsive breakpoints.
class Breakpoints {
  Breakpoints._();
  static const double phone = 480;
  static const double tablet = 820;
  static bool isTablet(double width) => width >= tablet;
}
