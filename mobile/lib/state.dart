import 'package:flutter/foundation.dart';
import 'api.dart';
import 'models.dart';

enum Stage { welcome, capture, consistency, eligibility, fill, teachback, output }

/// Drives the whole flow; mirrors the backend session state machine.
class AppState extends ChangeNotifier {
  final Api api = Api();

  String lang = 'hi';
  bool operator = false;
  Stage stage = Stage.welcome;
  bool busy = false;
  String? error;

  String? sid;
  String? selectedScheme;
  List<Persona> personas = [];

  CaptureResult? capture;
  Eligibility? eligibility;
  FormFill? form;
  TeachBack? teach;
  Output? output;

  void setLang(String l) { lang = l; notifyListeners(); }
  void toggleOperator() { operator = !operator; notifyListeners(); }

  Future<void> _guard(Future<void> Function() fn) async {
    busy = true; error = null; notifyListeners();
    try {
      await fn();
    } catch (e) {
      error = e.toString();
    } finally {
      busy = false; notifyListeners();
    }
  }

  Future<void> loadPersonas() => _guard(() async {
        personas = await api.personas();
      });

  Future<void> startWithPersona(String persona) => _guard(() async {
        sid = await api.createSession(lang, operator: operator);
        stage = Stage.capture; notifyListeners();
        capture = await api.capturePersona(sid!, persona);
        if (capture!.mismatches.isNotEmpty) {
          stage = Stage.consistency;
        } else {
          eligibility = await api.eligibility(sid!);
          stage = Stage.eligibility;
        }
      });

  Future<void> startWithDocuments(List<Map<String, dynamic>> docs, String? asked) => _guard(() async {
        sid = await api.createSession(lang, operator: operator);
        stage = Stage.capture; notifyListeners();
        capture = await api.captureDocuments(sid!, docs, asked);
        if (capture!.mismatches.isNotEmpty) {
          stage = Stage.consistency;
        } else {
          eligibility = await api.eligibility(sid!);
          stage = Stage.eligibility;
        }
      });

  Future<void> resolve(Map<String, dynamic> resolutions) => _guard(() async {
        await api.resolve(sid!, resolutions);
        eligibility = await api.eligibility(sid!);
        stage = Stage.eligibility;
      });

  Future<void> pickScheme(String schemeId) => _guard(() async {
        selectedScheme = schemeId;
        form = await api.selectForm(sid!, schemeId);
        stage = Stage.fill;
      });

  Future<void> answer(Map<String, dynamic> answers) => _guard(() async {
        await api.answer(sid!, answers);
        form = await api.selectForm(sid!, selectedScheme!);
      });

  Future<void> toTeachBack() => _guard(() async {
        teach = await api.teachback(sid!);
        stage = Stage.teachback;
      });

  Future<void> confirm(String method) => _guard(() async {
        output = await api.consent(sid!, confirmed: true, method: method);
        stage = Stage.output;
      });

  Future<void> setReference(String reference) async {
    if (output != null) await api.setReference(output!.trackingId, reference);
  }

  void reset() {
    stage = Stage.welcome;
    sid = null;
    selectedScheme = null;
    capture = null;
    eligibility = null;
    form = null;
    teach = null;
    output = null;
    error = null;
    notifyListeners();
  }
}
