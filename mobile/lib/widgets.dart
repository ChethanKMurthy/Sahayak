import 'package:flutter/material.dart';
import 'theme.dart';

/// Confidence-tier dot with optional pulse (green/amber/red).
class TierDot extends StatefulWidget {
  final String tier;
  final bool pulse;
  const TierDot(this.tier, {super.key, this.pulse = false});
  @override
  State<TierDot> createState() => _TierDotState();
}

class _TierDotState extends State<TierDot> with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: const Duration(milliseconds: 1600))..repeat();
  @override
  void dispose() { _c.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    final color = tierColor(widget.tier);
    return SizedBox(
      width: 14, height: 14,
      child: Stack(alignment: Alignment.center, children: [
        if (widget.pulse)
          AnimatedBuilder(
            animation: _c,
            builder: (_, __) => Container(
              width: 14 * (1 + _c.value * 1.4), height: 14 * (1 + _c.value * 1.4),
              decoration: BoxDecoration(
                shape: BoxShape.circle, color: color.withOpacity((1 - _c.value) * 0.5)),
            ),
          ),
        Container(width: 12, height: 12, decoration: BoxDecoration(shape: BoxShape.circle, color: color)),
      ]),
    );
  }
}

/// Animated scan frame — the phone-as-counter motif.
class ScanFrame extends StatefulWidget {
  final bool scanning;
  const ScanFrame({super.key, this.scanning = true});
  @override
  State<ScanFrame> createState() => _ScanFrameState();
}

class _ScanFrameState extends State<ScanFrame> with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: const Duration(seconds: 2))..repeat(reverse: true);
  @override
  void dispose() { _c.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 1.6,
      child: Container(
        decoration: BoxDecoration(
          color: C.sunk,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: C.saffron.withOpacity(0.4), width: 2, style: BorderStyle.solid),
        ),
        child: Stack(children: [
          const Center(child: Icon(Icons.description_outlined, size: 64, color: C.inkFaint)),
          if (widget.scanning)
            AnimatedBuilder(
              animation: _c,
              builder: (_, __) => Positioned(
                left: 0, right: 0, top: 12 + _c.value * 180,
                child: Container(
                  height: 2,
                  decoration: BoxDecoration(color: C.saffron, boxShadow: [
                    BoxShadow(color: C.saffron.withOpacity(0.6), blurRadius: 14, spreadRadius: 2)
                  ]),
                ),
              ),
            ),
        ]),
      ),
    );
  }
}

/// Pulsing voice orb.
class VoiceOrb extends StatefulWidget {
  final bool active;
  final VoidCallback? onTap;
  final String? label;
  const VoiceOrb({super.key, this.active = false, this.onTap, this.label});
  @override
  State<VoiceOrb> createState() => _VoiceOrbState();
}

class _VoiceOrbState extends State<VoiceOrb> with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: const Duration(milliseconds: 1800))..repeat();
  @override
  void dispose() { _c.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    return Column(mainAxisSize: MainAxisSize.min, children: [
      GestureDetector(
        onTap: widget.onTap,
        child: SizedBox(
          width: 120, height: 120,
          child: Stack(alignment: Alignment.center, children: [
            if (widget.active)
              ...List.generate(3, (i) => AnimatedBuilder(
                    animation: _c,
                    builder: (_, __) {
                      final v = ((_c.value + i / 3) % 1.0);
                      return Container(
                        width: 96 * (1 + v), height: 96 * (1 + v),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: C.saffron.withOpacity((1 - v) * 0.6), width: 2),
                        ),
                      );
                    },
                  )),
            Container(
              width: 96, height: 96,
              decoration: const BoxDecoration(shape: BoxShape.circle, color: C.saffron),
              child: const Icon(Icons.mic, color: Colors.white, size: 40),
            ),
          ]),
        ),
      ),
      if (widget.label != null) ...[
        const SizedBox(height: 10),
        Text(widget.label!, style: const TextStyle(color: C.inkSoft, fontWeight: FontWeight.w600)),
      ],
    ]);
  }
}

class SectionTitle extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? sub;
  const SectionTitle(this.icon, this.title, {super.key, this.sub});
  @override
  Widget build(BuildContext context) {
    return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Container(
        padding: const EdgeInsets.all(8),
        decoration: const BoxDecoration(color: C.saffronSoft, shape: BoxShape.circle),
        child: Icon(icon, color: C.saffronDeep, size: 20),
      ),
      const SizedBox(width: 12),
      Expanded(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700, height: 1.1)),
          if (sub != null) Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(sub!, style: const TextStyle(color: C.inkSoft, fontSize: 13)),
          ),
        ]),
      ),
    ]);
  }
}

class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  const AppCard({super.key, required this.child, this.padding = const EdgeInsets.all(16)});
  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: padding,
        decoration: BoxDecoration(
          color: C.card,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [BoxShadow(color: C.ink.withOpacity(0.06), blurRadius: 24, offset: const Offset(0, 8))],
        ),
        child: child,
      );
}
