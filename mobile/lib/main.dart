import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import 'i18n.dart';
import 'models.dart';
import 'screens/camera_capture.dart';
import 'services/voice.dart';
import 'state.dart';
import 'theme.dart';
import 'widgets.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await I18n.load();
  // Best-effort voice init (mic permission is requested on first use).
  VoiceSingleton.instance.init();
  runApp(ChangeNotifierProvider(create: (_) => AppState()..loadPersonas(), child: const SahayakApp()));
}

class SahayakApp extends StatelessWidget {
  const SahayakApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sahayak',
      debugShowCheckedModeBanner: false,
      theme: sahayakTheme(),
      home: const FlowScaffold(),
    );
  }
}

class FlowScaffold extends StatelessWidget {
  const FlowScaffold({super.key});
  @override
  Widget build(BuildContext context) {
    final s = context.watch<AppState>();
    return Scaffold(
      appBar: _bar(context, s),
      body: SafeArea(
        child: Column(children: [
          if (s.stage != Stage.welcome) _stepRail(s),
          if (s.error != null)
            Container(
              margin: const EdgeInsets.all(12), padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: C.flagSoft, borderRadius: BorderRadius.circular(12)),
              child: Text(s.error!, style: const TextStyle(color: C.flag, fontSize: 12)),
            ),
          Expanded(
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 320),
              transitionBuilder: (child, anim) => FadeTransition(
                opacity: anim,
                child: SlideTransition(
                  position: Tween(begin: const Offset(0, 0.04), end: Offset.zero).animate(anim),
                  child: child),
              ),
              child: _stageView(context, s),
            ),
          ),
        ]),
      ),
    );
  }

  PreferredSizeWidget _bar(BuildContext context, AppState s) => AppBar(
        titleSpacing: 16,
        title: Row(children: [
          Container(
            width: 36, height: 36, alignment: Alignment.center,
            decoration: BoxDecoration(color: C.saffron, borderRadius: BorderRadius.circular(10)),
            child: const Text('स', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          ),
          const SizedBox(width: 10),
          Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
            Text(I18n.t('app_name', s.lang), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            Text(I18n.t('tagline', s.lang), style: const TextStyle(fontSize: 10, color: C.inkFaint)),
          ]),
        ]),
        actions: [
          if (s.stage != Stage.welcome)
            IconButton(onPressed: () => context.read<AppState>().reset(), icon: const Icon(Icons.home_outlined)),
          PopupMenuButton<String>(
            initialValue: s.lang,
            onSelected: (l) => context.read<AppState>().setLang(l),
            itemBuilder: (_) => I18n.languages
                .map((e) => PopupMenuItem(value: e.$1, child: Text(e.$2)))
                .toList(),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Row(children: [
                Text(I18n.languages.firstWhere((e) => e.$1 == s.lang).$2,
                    style: const TextStyle(fontWeight: FontWeight.w600)),
                const Icon(Icons.arrow_drop_down),
              ]),
            ),
          ),
        ],
      );

  Widget _stepRail(AppState s) {
    const order = [Stage.capture, Stage.consistency, Stage.eligibility, Stage.fill, Stage.teachback, Stage.output];
    final idx = order.indexOf(s.stage);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      child: Row(
        children: List.generate(order.length, (i) => Expanded(
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 2),
            height: 6,
            decoration: BoxDecoration(
              color: i <= idx ? C.saffron : C.sunk, borderRadius: BorderRadius.circular(99)),
          ),
        )),
      ),
    );
  }

  Widget _stageView(BuildContext context, AppState s) {
    switch (s.stage) {
      case Stage.welcome: return const WelcomeScreen(key: ValueKey('welcome'));
      case Stage.capture: return CaptureScreen(key: const ValueKey('capture'), s: s);
      case Stage.consistency: return ConsistencyScreen(key: const ValueKey('consistency'), s: s);
      case Stage.eligibility: return EligibilityScreen(key: const ValueKey('eligibility'), s: s);
      case Stage.fill: return FillScreen(key: const ValueKey('fill'), s: s);
      case Stage.teachback: return TeachBackScreen(key: const ValueKey('teachback'), s: s);
      case Stage.output: return OutputScreen(key: const ValueKey('output'), s: s);
    }
  }
}

/* ───────────────────────────── Welcome ──────────────────────────────────── */
class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});
  @override
  Widget build(BuildContext context) {
    final s = context.watch<AppState>();
    return ListView(padding: const EdgeInsets.all(20), children: [
      const SizedBox(height: 8),
      Text(I18n.t('tagline', s.lang),
          style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w800, height: 1.1)),
      const SizedBox(height: 8),
      const Text(
        'Place your documents, speak one answer in your language, and out comes a correctly-filled, submittable application — plus the schemes you didn\'t know you qualified for.',
        style: TextStyle(color: C.inkSoft)),
      const SizedBox(height: 16),
      AppCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.verified_user_outlined, color: C.leaf, size: 18),
            const SizedBox(width: 8),
            Expanded(child: Text(I18n.t('aadhaar_safe', s.lang),
                style: const TextStyle(fontSize: 12, color: C.inkSoft, fontWeight: FontWeight.w600))),
          ]),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: () async {
              final docs = await Navigator.of(context).push<List<Map<String, dynamic>>>(
                MaterialPageRoute(builder: (_) => CameraCaptureScreen(lang: s.lang)),
              );
              if (docs != null && docs.isNotEmpty && context.mounted) {
                context.read<AppState>().startWithDocuments(docs, null);
              }
            },
            icon: const Icon(Icons.camera_alt_outlined),
            label: Text(I18n.t('capture', s.lang)),
          ),
        ]),
      ),
      const SizedBox(height: 16),
      const Text('Or try a demo profile (synthetic data — no real PII):',
          style: TextStyle(fontWeight: FontWeight.w600)),
      const SizedBox(height: 10),
      if (s.personas.isEmpty)
        const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator())),
      ...s.personas.map((p) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: InkWell(
              borderRadius: BorderRadius.circular(20),
              onTap: s.busy ? null : () => context.read<AppState>().startWithPersona(p.id),
              child: AppCard(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(I18n.loc(p.label, s.lang), style: const TextStyle(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 4),
                  Text('Came asking about: ${p.askedScheme.replaceAll('-', ' ')}',
                      style: const TextStyle(color: C.saffron, fontSize: 12)),
                ]),
              ),
            ),
          )),
    ]);
  }
}

/* ───────────────────────────── Capture ──────────────────────────────────── */
class CaptureScreen extends StatelessWidget {
  final AppState s;
  const CaptureScreen({super.key, required this.s});
  @override
  Widget build(BuildContext context) {
    return ListView(padding: const EdgeInsets.all(20), children: [
      SectionTitle(Icons.document_scanner_outlined, I18n.t('capture', s.lang), sub: I18n.t('place_document', s.lang)),
      const SizedBox(height: 16),
      ScanFrame(scanning: s.capture == null || s.busy),
      const SizedBox(height: 16),
      if (s.capture == null)
        Center(child: Text(I18n.t('extracting', s.lang), style: const TextStyle(color: C.inkSoft)))
      else
        ...s.capture!.documents.map((d) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: AppCard(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                    Text(d.type.replaceAll('_', ' ').toUpperCase(),
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                    _pill('OCR ${(d.ocrQuality * 100).round()}%', d.ocrQuality > 0.85 ? C.leaf : C.saffron),
                  ]),
                  const SizedBox(height: 8),
                  Wrap(spacing: 6, runSpacing: 6, children: d.fields.map((f) => Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: C.sunk, borderRadius: BorderRadius.circular(8)),
                        child: Text('${f.key.replaceAll('_', ' ')}: ${f.value}',
                            style: const TextStyle(fontSize: 12)),
                      )).toList()),
                ]),
              ),
            )),
    ]);
  }
}

Widget _pill(String text, Color color) => Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: color.withOpacity(0.12), borderRadius: BorderRadius.circular(99)),
      child: Text(text, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w700)),
    );

/* ───────────────────────────── Consistency ──────────────────────────────── */
class ConsistencyScreen extends StatefulWidget {
  final AppState s;
  const ConsistencyScreen({super.key, required this.s});
  @override
  State<ConsistencyScreen> createState() => _ConsistencyScreenState();
}

class _ConsistencyScreenState extends State<ConsistencyScreen> {
  final Map<String, dynamic> choices = {};
  @override
  Widget build(BuildContext context) {
    final s = widget.s;
    final m = s.capture!.mismatches;
    final allChosen = m.every((mm) => choices.containsKey(mm.field));
    return ListView(padding: const EdgeInsets.all(20), children: [
      SectionTitle(Icons.info_outline, I18n.t('review_mismatch', s.lang),
          sub: 'We found the same detail spelled differently — the #1 cause of rejection.'),
      const SizedBox(height: 16),
      ...m.map((mm) => Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: AppCard(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(I18n.loc(mm.question, s.lang), style: const TextStyle(fontWeight: FontWeight.w600)),
                const SizedBox(height: 10),
                ...mm.values.map((v) {
                  final picked = choices[mm.field] == v['value'];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(14),
                      onTap: () => setState(() => choices[mm.field] = v['value']),
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: picked ? C.saffronSoft : C.paper,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: picked ? C.saffron : C.inkFaint.withOpacity(0.3)),
                        ),
                        child: Row(children: [
                          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text('${v['value']}', style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                            Text('from ${(v['doc_type'] as String).replaceAll('_', ' ')}',
                                style: const TextStyle(fontSize: 11, color: C.inkFaint)),
                          ])),
                          if (picked) const Icon(Icons.check_circle, color: C.saffron),
                        ]),
                      ),
                    ),
                  );
                }),
              ]),
            ),
          )),
      const SizedBox(height: 8),
      FilledButton(
        onPressed: allChosen && !s.busy ? () => context.read<AppState>().resolve(choices) : null,
        child: const Text('Confirm and continue'),
      ),
    ]);
  }
}

/* ───────────────────────────── Eligibility ──────────────────────────────── */
class EligibilityScreen extends StatelessWidget {
  final AppState s;
  const EligibilityScreen({super.key, required this.s});
  @override
  Widget build(BuildContext context) {
    final e = s.eligibility!;
    return ListView(padding: const EdgeInsets.all(20), children: [
      SectionTitle(Icons.account_balance_outlined, 'What you\'re entitled to',
          sub: 'Checked in code against the rules — not guessed.'),
      const SizedBox(height: 16),
      if (e.qualifies.isNotEmpty) ...[
        Text(I18n.t('you_qualify', s.lang), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        ...e.qualifies.map((x) => _schemeCard(context, x, C.leaf, false)),
      ],
      if (e.surprises.isNotEmpty) ...[
        const SizedBox(height: 16),
        Row(children: [
          const Icon(Icons.auto_awesome, color: C.saffron, size: 20),
          const SizedBox(width: 6),
          Expanded(child: Text(I18n.t('also_qualify', s.lang),
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700))),
        ]),
        const SizedBox(height: 8),
        ...e.surprises.map((x) => _schemeCard(context, x, C.saffron, true)),
      ],
      if (e.dependencies.isNotEmpty) ...[
        const SizedBox(height: 16),
        Text(I18n.t('need_first', s.lang), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        ...e.dependencies.map((d) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: C.amberSoft, borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: C.amber.withOpacity(0.3))),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(d.schemeName, style: const TextStyle(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 8),
                  Wrap(spacing: 8, runSpacing: 8, children: [
                    const Text('requires', style: TextStyle(color: C.inkSoft)),
                    ...d.needs.map((n) => ActionChip(
                          label: Text('${n['scheme_name']} →'),
                          backgroundColor: C.card,
                          labelStyle: const TextStyle(color: C.amber, fontWeight: FontWeight.w600),
                          onPressed: () => context.read<AppState>().pickScheme(n['scheme_id']),
                        )),
                  ]),
                ]),
              ),
            )),
      ],
      if (e.certificates.isNotEmpty) ...[
        const SizedBox(height: 14),
        Text('You can also obtain: ${e.certificates.map((c) => c.schemeName).join(', ')}.',
            style: const TextStyle(color: C.inkFaint, fontSize: 12)),
      ],
    ]);
  }

  Widget _schemeCard(BuildContext context, EligItem x, Color tone, bool highlight) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: () => context.read<AppState>().pickScheme(x.schemeId),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: highlight ? C.saffronSoft : C.card,
              borderRadius: BorderRadius.circular(20),
              border: highlight ? Border.all(color: C.saffron.withOpacity(0.3)) : null,
              boxShadow: [BoxShadow(color: C.ink.withOpacity(0.06), blurRadius: 18, offset: const Offset(0, 6))],
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(color: tone.withOpacity(0.12), shape: BoxShape.circle),
                  child: Icon(Icons.workspace_premium_outlined, color: tone, size: 18),
                ),
                const SizedBox(width: 10),
                Expanded(child: Text(x.schemeName, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16))),
              ]),
              const SizedBox(height: 8),
              Text(x.benefit, style: const TextStyle(color: C.inkSoft, fontSize: 13)),
              const SizedBox(height: 4),
              Text(x.why, style: const TextStyle(color: C.inkFaint, fontSize: 11)),
              const SizedBox(height: 6),
              Text('${I18n.t('fill_form', s.lang)} →',
                  style: const TextStyle(color: C.saffron, fontWeight: FontWeight.w700)),
            ]),
          ),
        ),
      );
}

/* ───────────────────────────── Fill ─────────────────────────────────────── */
class FillScreen extends StatefulWidget {
  final AppState s;
  const FillScreen({super.key, required this.s});
  @override
  State<FillScreen> createState() => _FillScreenState();
}

class _FillScreenState extends State<FillScreen> {
  String? openSource;
  final voice = VoiceSingleton.instance;

  Future<void> _askByVoice(GapQuestion q) async {
    await voice.speak(q.question, widget.s.lang);
    final said = voice.available ? await voice.listen(widget.s.lang) : '';
    if (said.isNotEmpty && mounted) {
      context.read<AppState>().answer({q.key: _coerce(said)});
    }
  }

  @override
  Widget build(BuildContext context) {
    final f = widget.s.form!;
    return ListView(padding: const EdgeInsets.all(20), children: [
      SectionTitle(Icons.receipt_long_outlined, f.title,
          sub: 'Tap a field to see where its value came from. Only ? and ! need your check.'),
      const SizedBox(height: 16),
      AppCard(
        padding: EdgeInsets.zero,
        child: Column(children: f.filled.map((field) {
          final open = openSource == field.key;
          final empty = field.missing || field.value == null || '${field.value}'.isEmpty;
          return Column(children: [
            ListTile(
              leading: TierDot(field.tier, pulse: field.tier != 'green' && !empty),
              title: Text(field.label, style: const TextStyle(fontSize: 12, color: C.inkFaint)),
              subtitle: Text(empty ? '—' : '${field.value}',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600,
                      fontStyle: empty ? FontStyle.italic : FontStyle.normal)),
              trailing: empty && field.required
                  ? null
                  : _pill(I18n.t('tier_${field.tier}', widget.s.lang), tierColor(field.tier)),
              onTap: () => setState(() => openSource = open ? null : field.key),
            ),
            if (open)
              Container(
                width: double.infinity,
                margin: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(color: C.sunk, borderRadius: BorderRadius.circular(10)),
                child: Text('${I18n.t('source_label', widget.s.lang)}: ${field.source.isEmpty ? '—' : field.source}',
                    style: const TextStyle(fontSize: 12, color: C.inkSoft)),
              ),
          ]);
        }).toList()),
      ),
      const SizedBox(height: 16),
      if (f.missing.isNotEmpty)
        AppCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('A few details we couldn\'t read — answer by voice or tap:',
                style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            ...f.missing.map((q) => Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      const Icon(Icons.volume_up_outlined, color: C.saffron, size: 18),
                      const SizedBox(width: 6),
                      Expanded(child: Text(q.question, style: const TextStyle(fontWeight: FontWeight.w600))),
                    ]),
                    const SizedBox(height: 8),
                    if (q.options.isNotEmpty)
                      Wrap(spacing: 8, children: q.options.map((o) => ActionChip(
                            label: Text(o),
                            onPressed: () => context.read<AppState>().answer({q.key: _coerce(o)}),
                          )).toList())
                    else
                      Row(children: [
                        OutlinedButton.icon(
                          onPressed: () => _askByVoice(q),
                          icon: const Icon(Icons.mic), label: Text(I18n.t('speak_now', widget.s.lang))),
                        const SizedBox(width: 8),
                        Expanded(child: _TypeField(onSubmit: (v) =>
                            context.read<AppState>().answer({q.key: _coerce(v)}))),
                      ]),
                  ]),
                )),
          ]),
        )
      else
        FilledButton.icon(
          onPressed: widget.s.busy ? null : () => context.read<AppState>().toTeachBack(),
          icon: const Icon(Icons.volume_up),
          label: Text(I18n.t('read_back', widget.s.lang)),
        ),
    ]);
  }
}

class _TypeField extends StatefulWidget {
  final void Function(String) onSubmit;
  const _TypeField({required this.onSubmit});
  @override
  State<_TypeField> createState() => _TypeFieldState();
}

class _TypeFieldState extends State<_TypeField> {
  final c = TextEditingController();
  @override
  Widget build(BuildContext context) => TextField(
        controller: c,
        decoration: InputDecoration(
          hintText: 'type answer',
          isDense: true,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(99)),
          suffixIcon: IconButton(
            icon: const Icon(Icons.send),
            onPressed: () { if (c.text.isNotEmpty) { widget.onSubmit(c.text); c.clear(); } }),
        ),
        onSubmitted: (v) { if (v.isNotEmpty) { widget.onSubmit(v); c.clear(); } },
      );
}

/* ───────────────────────────── Teach-back ───────────────────────────────── */
class TeachBackScreen extends StatefulWidget {
  final AppState s;
  const TeachBackScreen({super.key, required this.s});
  @override
  State<TeachBackScreen> createState() => _TeachBackScreenState();
}

class _TeachBackScreenState extends State<TeachBackScreen> {
  final voice = VoiceSingleton.instance;
  int active = -1;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _play());
  }

  Future<void> _play() async {
    final lines = widget.s.teach!.lines;
    for (var i = 0; i < lines.length; i++) {
      if (!mounted) return;
      setState(() => active = i);
      await voice.speak(lines[i]['text'].toString(), widget.s.lang);
    }
    if (mounted) setState(() => active = -1);
  }

  Future<void> _confirmByVoice() async {
    final said = voice.available ? await voice.listen(widget.s.lang) : 'yes';
    if (RegExp(r'yes|haan|हाँ|ಹೌದು|ஆம்|అవును|হ্যাঁ|होय', caseSensitive: false).hasMatch(said)) {
      if (mounted) context.read<AppState>().confirm('voice');
    }
  }

  @override
  void dispose() { voice.stop(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final lines = widget.s.teach!.lines;
    return ListView(padding: const EdgeInsets.all(20), children: [
      SectionTitle(Icons.campaign_outlined, I18n.t('read_back', widget.s.lang),
          sub: 'We read your form aloud. Nothing is produced until you confirm — we never auto-submit.'),
      const SizedBox(height: 16),
      AppCard(
        child: Column(children: List.generate(lines.length, (i) {
          final l = lines[i];
          final on = active == i;
          return AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            margin: const EdgeInsets.symmetric(vertical: 2),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              color: on ? C.saffronSoft : Colors.transparent, borderRadius: BorderRadius.circular(10)),
            child: Row(children: [
              TierDot(l['tier'].toString(), pulse: on),
              const SizedBox(width: 8),
              Expanded(child: Text(l['text'].toString(),
                  style: TextStyle(fontWeight: on ? FontWeight.w700 : FontWeight.w400))),
            ]),
          );
        })),
      ),
      const SizedBox(height: 16),
      OutlinedButton.icon(onPressed: _play, icon: const Icon(Icons.replay), label: const Text('Play again')),
      const SizedBox(height: 10),
      FilledButton.icon(onPressed: _confirmByVoice, icon: const Icon(Icons.mic),
          label: const Text('Say "yes" to confirm')),
      const SizedBox(height: 10),
      OutlinedButton.icon(
        onPressed: widget.s.busy ? null : () => context.read<AppState>().confirm('tap'),
        icon: const Icon(Icons.check),
        label: Text(I18n.t('confirm_consent', widget.s.lang)),
      ),
    ]);
  }
}

/* ───────────────────────────── Output ───────────────────────────────────── */
class OutputScreen extends StatefulWidget {
  final AppState s;
  const OutputScreen({super.key, required this.s});
  @override
  State<OutputScreen> createState() => _OutputScreenState();
}

class _OutputScreenState extends State<OutputScreen> {
  final refCtl = TextEditingController();
  bool tracked = false;

  @override
  Widget build(BuildContext context) {
    final o = widget.s.output!;
    final fp = o.fairPrice;
    return ListView(padding: const EdgeInsets.all(20), children: [
      Center(child: Column(children: [
        Container(
          width: 64, height: 64,
          decoration: const BoxDecoration(color: C.leafSoft, shape: BoxShape.circle),
          child: const Icon(Icons.check, color: C.leaf, size: 36)),
        const SizedBox(height: 8),
        const Text('Your application is ready',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
        const Text('A draft for your confirmation — not auto-submitted.',
            style: TextStyle(color: C.inkSoft)),
      ])),
      const SizedBox(height: 16),
      FilledButton.icon(
        onPressed: () => launchUrl(Uri.parse(widget.s.api.fileUrl(o.pdfUrl)),
            mode: LaunchMode.externalApplication),
        icon: const Icon(Icons.file_download_outlined),
        label: Text(I18n.t('download_pdf', widget.s.lang)),
      ),
      const SizedBox(height: 16),
      AppCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(I18n.t('checklist', widget.s.lang),
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        ...o.checklist.map((c) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('☐  '),
                Expanded(child: Text('${c['instruction']} ${c['label']}'
                    '${(c['note'] ?? '').toString().isNotEmpty ? ' — ${c['note']}' : ''}')),
              ]),
            )),
      ])),
      const SizedBox(height: 12),
      AppCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Icon(Icons.place_outlined, color: C.saffron),
          const SizedBox(width: 6),
          Text(I18n.t('where_submit', widget.s.lang),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
        ]),
        const SizedBox(height: 6),
        Text(o.submitTo, style: const TextStyle(color: C.inkSoft)),
        if (o.onlineWall) Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(color: C.amberSoft, borderRadius: BorderRadius.circular(10)),
            child: Text('⚠ ${o.onlineWallNote}', style: const TextStyle(color: C.amber, fontSize: 12)),
          ),
        ),
      ])),
      const SizedBox(height: 12),
      AppCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(I18n.t('fair_price', widget.s.lang),
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
        const SizedBox(height: 12),
        Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
          _bar('Official', (fp['official_fee'] ?? 0).toDouble(), (fp['tout_price'] ?? 1).toDouble(), C.leaf),
          const SizedBox(width: 16),
          _bar('Typical tout', (fp['tout_price'] ?? 0).toDouble(), (fp['tout_price'] ?? 1).toDouble(), C.flag),
        ]),
        const SizedBox(height: 10),
        Center(child: Text('You save ₹${fp['you_save'] ?? 0}',
            style: const TextStyle(color: C.leaf, fontWeight: FontWeight.w700))),
      ])),
      const SizedBox(height: 12),
      AppCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(I18n.t('track', widget.s.lang),
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        if (tracked)
          const Text("Saved. We'll remind you to follow up in 30 days.",
              style: TextStyle(color: C.leaf))
        else
          Row(children: [
            Expanded(child: TextField(
              controller: refCtl,
              decoration: InputDecoration(
                hintText: 'Acknowledgement / reference number',
                isDense: true,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(99))),
            )),
            const SizedBox(width: 8),
            FilledButton(
              onPressed: () async {
                if (refCtl.text.isEmpty) return;
                await context.read<AppState>().setReference(refCtl.text);
                setState(() => tracked = true);
              },
              child: const Text('Save')),
          ]),
      ])),
    ]);
  }

  Widget _bar(String label, double value, double max, Color color) {
    final pct = max > 0 ? (value / max).clamp(0.04, 1.0) : 0.04;
    return Expanded(
      child: Column(children: [
        SizedBox(
          height: 100,
          child: Align(
            alignment: Alignment.bottomCenter,
            child: FractionallySizedBox(
              heightFactor: pct.toDouble(),
              child: Container(decoration: BoxDecoration(
                color: color, borderRadius: const BorderRadius.vertical(top: Radius.circular(8)))),
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text('₹${value.toInt()}', style: const TextStyle(fontWeight: FontWeight.w700)),
        Text(label, style: const TextStyle(fontSize: 11, color: C.inkFaint)),
      ]),
    );
  }
}

/* helpers */
dynamic _coerce(String v) {
  final t = v.trim();
  if (t.toLowerCase() == 'true' || t.toLowerCase() == 'yes') return true;
  if (t.toLowerCase() == 'false' || t.toLowerCase() == 'no') return false;
  final n = num.tryParse(t);
  return n ?? t;
}
