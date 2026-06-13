/// A lightweight Result type for network/API calls, so failures are values the
/// UI handles explicitly instead of exceptions leaking through the widget tree.
sealed class ApiResult<T> {
  const ApiResult();

  R when<R>({
    required R Function(T data) success,
    required R Function(String message, Object? error) failure,
  }) {
    final self = this;
    if (self is ApiSuccess<T>) return success(self.data);
    self as ApiFailure<T>;
    return failure(self.message, self.error);
  }

  bool get isSuccess => this is ApiSuccess<T>;
}

class ApiSuccess<T> extends ApiResult<T> {
  final T data;
  const ApiSuccess(this.data);
}

class ApiFailure<T> extends ApiResult<T> {
  final String message;
  final Object? error;
  const ApiFailure(this.message, [this.error]);
}

/// Run an async call and map any thrown error to a friendly [ApiFailure].
Future<ApiResult<T>> guardApi<T>(Future<T> Function() call) async {
  try {
    return ApiSuccess<T>(await call());
  } catch (e) {
    return ApiFailure<T>(_friendly(e), e);
  }
}

String _friendly(Object e) {
  final s = e.toString();
  if (s.contains('SocketException') || s.contains('Failed host lookup')) {
    return 'No internet connection. Please check your network and try again.';
  }
  if (s.contains('TimeoutException')) {
    return 'The server took too long to respond. Please try again.';
  }
  return 'Something went wrong. Please try again.';
}
