// Plain data models mirroring the backend API.
class Persona {
  final String id;
  final Map<String, dynamic> label;
  final String askedScheme;
  Persona(this.id, this.label, this.askedScheme);
  factory Persona.fromJson(Map<String, dynamic> j) =>
      Persona(j['id'], j['label'] ?? {}, j['asked_scheme'] ?? '');
}

class ExtractedField {
  final String key;
  final dynamic value;
  final double ocrConfidence;
  ExtractedField(this.key, this.value, this.ocrConfidence);
  factory ExtractedField.fromJson(Map<String, dynamic> j) =>
      ExtractedField(j['key'], j['value'], (j['ocr_confidence'] ?? 1.0).toDouble());
  Map<String, dynamic> toJson() => {'key': key, 'value': value, 'ocr_confidence': ocrConfidence};
}

class Doc {
  final String id, type;
  final double ocrQuality;
  final List<ExtractedField> fields;
  final String? recaptureHint;
  Doc(this.id, this.type, this.ocrQuality, this.fields, this.recaptureHint);
  factory Doc.fromJson(Map<String, dynamic> j) => Doc(
        j['id'], j['type'], (j['ocr_quality'] ?? 1.0).toDouble(),
        (j['fields'] as List).map((f) => ExtractedField.fromJson(f)).toList(),
        j['recapture_hint']);
}

class Mismatch {
  final String field;
  final List<Map<String, dynamic>> values;
  final Map<String, dynamic> question;
  Mismatch(this.field, this.values, this.question);
  factory Mismatch.fromJson(Map<String, dynamic> j) => Mismatch(
        j['field'], (j['values'] as List).cast<Map<String, dynamic>>(), j['question'] ?? {});
}

class CaptureResult {
  final List<Doc> documents;
  final List<Mismatch> mismatches;
  final List<Map<String, dynamic>> recapture;
  final String state;
  CaptureResult(this.documents, this.mismatches, this.recapture, this.state);
  factory CaptureResult.fromJson(Map<String, dynamic> j) => CaptureResult(
        (j['documents'] as List).map((d) => Doc.fromJson(d)).toList(),
        (j['mismatches'] as List).map((m) => Mismatch.fromJson(m)).toList(),
        (j['recapture'] as List).cast<Map<String, dynamic>>(),
        j['state']);
}

class EligItem {
  final String schemeId, status, schemeName, category, benefit, why;
  final List<dynamic> missingPrerequisites;
  EligItem(this.schemeId, this.status, this.schemeName, this.category, this.benefit, this.why,
      this.missingPrerequisites);
  factory EligItem.fromJson(Map<String, dynamic> j) => EligItem(
        j['scheme_id'], j['status'], j['scheme_name'] ?? j['scheme_id'], j['category'] ?? '',
        j['benefit'] ?? '', j['why'] ?? '', j['missing_prerequisites'] ?? []);
}

class Dependency {
  final String schemeId, schemeName;
  final List<Map<String, dynamic>> needs;
  final List<dynamic> needsDocuments;
  Dependency(this.schemeId, this.schemeName, this.needs, this.needsDocuments);
  factory Dependency.fromJson(Map<String, dynamic> j) => Dependency(
        j['scheme_id'], j['scheme_name'] ?? j['scheme_id'],
        (j['needs'] as List).cast<Map<String, dynamic>>(), j['needs_documents'] ?? []);
}

class Eligibility {
  final List<EligItem> qualifies, needsPrerequisite, surprises, certificates;
  final List<Dependency> dependencies;
  Eligibility(this.qualifies, this.needsPrerequisite, this.surprises, this.certificates,
      this.dependencies);
  factory Eligibility.fromJson(Map<String, dynamic> j) {
    List<EligItem> p(String k) => (j[k] as List).map((e) => EligItem.fromJson(e)).toList();
    return Eligibility(p('qualifies'), p('needs_prerequisite'), p('surprises'), p('certificates'),
        (j['dependencies'] as List).map((d) => Dependency.fromJson(d)).toList());
  }
}

class FilledField {
  final String key, label, tier, source;
  final dynamic value;
  final bool required, selfDeclared, verified, missing;
  FilledField(this.key, this.label, this.tier, this.source, this.value, this.required,
      this.selfDeclared, this.verified, this.missing);
  factory FilledField.fromJson(Map<String, dynamic> j) => FilledField(
        j['key'], j['label'], j['tier'], j['source'] ?? '', j['value'],
        j['required'] ?? false, j['self_declared'] ?? false, j['verified'] ?? false,
        j['missing'] ?? false);
}

class GapQuestion {
  final String key, label, question, type;
  final List<String> options;
  GapQuestion(this.key, this.label, this.question, this.type, this.options);
  factory GapQuestion.fromJson(Map<String, dynamic> j) => GapQuestion(
        j['key'], j['label'], j['question'], j['type'] ?? 'text',
        (j['options'] as List).cast<String>());
}

class FormFill {
  final String formId, title, state;
  final List<FilledField> filled;
  final List<GapQuestion> missing;
  FormFill(this.formId, this.title, this.state, this.filled, this.missing);
  factory FormFill.fromJson(Map<String, dynamic> j) => FormFill(
        j['form_id'], j['title'], j['state'] ?? '',
        (j['filled'] as List).map((f) => FilledField.fromJson(f)).toList(),
        (j['missing'] as List).map((m) => GapQuestion.fromJson(m)).toList());
}

class TeachBack {
  final String script;
  final List<Map<String, dynamic>> lines;
  TeachBack(this.script, this.lines);
  factory TeachBack.fromJson(Map<String, dynamic> j) =>
      TeachBack(j['script'], (j['lines'] as List).cast<Map<String, dynamic>>());
}

class Output {
  final String pdfUrl, trackingId, submitTo;
  final bool onlineWall;
  final String onlineWallNote;
  final List<Map<String, dynamic>> checklist;
  final Map<String, dynamic> fairPrice;
  Output(this.pdfUrl, this.trackingId, this.submitTo, this.onlineWall, this.onlineWallNote,
      this.checklist, this.fairPrice);
  factory Output.fromJson(Map<String, dynamic> j) => Output(
        j['pdf_url'], j['tracking_id'], j['output']['submit_to'] ?? '',
        j['output']['online_wall'] ?? false, j['output']['online_wall_note'] ?? '',
        (j['checklist'] as List).cast<Map<String, dynamic>>(),
        j['output']['fair_price'] ?? {});
}
