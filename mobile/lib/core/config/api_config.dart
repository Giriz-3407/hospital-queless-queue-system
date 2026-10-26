/// Centralized API configuration for the Queueless mobile client.
/// Supports Android emulator (10.0.2.2), physical devices via Wi-Fi/LAN IP,
/// and production HTTPS endpoints via compile-time `--dart-define=API_BASE_URL=...`
/// or runtime updates.
class ApiConfig {
  ApiConfig._();

  /// Default backend URL targeting Android emulator host loopback.
  static const String defaultEmulatorUrl = 'http://10.0.2.2:5000/api/v1';

  /// Compile-time configurable URL, falling back to Android emulator URL.
  /// Example: flutter run --dart-define=API_BASE_URL=http://192.168.1.50:5000/api/v1
  static const String _envBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: defaultEmulatorUrl,
  );

  static String _activeBaseUrl = _envBaseUrl;

  /// The active base URL used by all network requests.
  static String get baseUrl => _activeBaseUrl;

  /// Update the base URL at runtime (e.g., for physical Wi-Fi testing without rebuild).
  static void setBaseUrl(String url) {
    var trimmed = url.trim();
    if (trimmed.endsWith('/')) {
      trimmed = trimmed.substring(0, trimmed.length - 1);
    }
    _activeBaseUrl = trimmed;
  }

  /// Reset to the default environment URL.
  static void resetToDefault() {
    _activeBaseUrl = _envBaseUrl;
  }

  // Timeouts
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 10);
  static const Duration sendTimeout = Duration(seconds: 10);

  // Common Endpoints
  static const String healthEndpoint = '/health';
  static const String registerEndpoint = '/auth/register';
  static const String loginEndpoint = '/auth/login';
  static const String meEndpoint = '/auth/me';
  static const String departmentsEndpoint = '/departments';
  static const String joinQueueEndpoint = '/queues/join';
  static const String myQueuesEndpoint = '/queues/my';
  static const String patientProfileEndpoint = '/patients/me';
  static const String patientQueuesEndpoint = '/patients/me/queues';

  static String queueByIdEndpoint(String id) => '/queues/$id';
  static String cancelQueueEndpoint(String id) => '/queues/$id/cancel';
  static String departmentByIdEndpoint(String id) => '/departments/$id';
  static String departmentQueueEndpoint(String id) => '/departments/$id/queue';
}
