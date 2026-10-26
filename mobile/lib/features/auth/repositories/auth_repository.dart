import '../../../core/config/api_config.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/secure_storage_service.dart';
import '../models/user_model.dart';

/// Repository for patient authentication and session lifecycle.
class AuthRepository {
  final ApiClient _client;
  final SecureStorageService _storage;

  AuthRepository({
    ApiClient? client,
    SecureStorageService? storage,
  })  : _client = client ?? ApiClient(),
        _storage = storage ?? SecureStorageService();

  /// Register a new patient. Role is strictly restricted to 'patient'.
  Future<AuthDataModel> register({
    required String name,
    required String email,
    required String password,
    String? phone,
  }) async {
    final response = await _client.post<AuthDataModel>(
      ApiConfig.registerEndpoint,
      data: {
        'name': name.trim(),
        'email': email.trim().toLowerCase(),
        'password': password,
        if (phone != null && phone.trim().isNotEmpty) 'phone': phone.trim(),
        'role': 'patient',
      },
      fromDataJson: (data) => AuthDataModel.fromJson(data as Map<String, dynamic>),
    );

    final authData = response.data!;
    await _storage.saveToken(authData.token);
    await _storage.saveUserSummary(
      id: authData.user.id,
      name: authData.user.name,
      email: authData.user.email,
      role: authData.user.role,
    );
    return authData;
  }

  /// Authenticate patient credentials and store JWT token securely.
  Future<AuthDataModel> login({
    required String email,
    required String password,
  }) async {
    final response = await _client.post<AuthDataModel>(
      ApiConfig.loginEndpoint,
      data: {
        'email': email.trim().toLowerCase(),
        'password': password,
      },
      fromDataJson: (data) => AuthDataModel.fromJson(data as Map<String, dynamic>),
    );

    final authData = response.data!;
    await _storage.saveToken(authData.token);
    await _storage.saveUserSummary(
      id: authData.user.id,
      name: authData.user.name,
      email: authData.user.email,
      role: authData.user.role,
    );
    return authData;
  }

  /// Fetch currently authenticated patient profile.
  Future<UserModel> getMe() async {
    final response = await _client.get<UserModel>(
      ApiConfig.meEndpoint,
      fromDataJson: (data) => UserModel.fromJson(data as Map<String, dynamic>),
    );
    return response.data!;
  }

  /// Sign out and clear stored JWT token and credentials.
  Future<void> logout() async {
    await _storage.clearAuth();
  }

  /// Check whether an authenticated session exists.
  Future<bool> isAuthenticated() async {
    return _storage.hasToken();
  }

  /// Get stored user summary if available.
  Future<Map<String, String?>> getStoredUserSummary() async {
    return _storage.getUserSummary();
  }
}
