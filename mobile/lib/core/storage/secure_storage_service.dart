import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Secure token and session persistence using Android KeyStore / FlutterSecureStorage.
/// Plaintext passwords or secrets are never persisted locally.
class SecureStorageService {
  final FlutterSecureStorage _storage;

  SecureStorageService({FlutterSecureStorage? storage})
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(),
            );

  static const String _keyToken = 'auth_token';
  static const String _keyUserId = 'user_id';
  static const String _keyUserName = 'user_name';
  static const String _keyUserEmail = 'user_email';
  static const String _keyUserRole = 'user_role';

  /// Save JWT access token securely.
  Future<void> saveToken(String token) async {
    await _storage.write(key: _keyToken, value: token);
  }

  /// Retrieve the saved JWT access token.
  Future<String?> getToken() async {
    return _storage.read(key: _keyToken);
  }

  /// Save current user summary fields.
  Future<void> saveUserSummary({
    required String id,
    required String name,
    required String email,
    required String role,
  }) async {
    await Future.wait([
      _storage.write(key: _keyUserId, value: id),
      _storage.write(key: _keyUserName, value: name),
      _storage.write(key: _keyUserEmail, value: email),
      _storage.write(key: _keyUserRole, value: role),
    ]);
  }

  /// Read user summary fields.
  Future<Map<String, String?>> getUserSummary() async {
    final values = await Future.wait([
      _storage.read(key: _keyUserId),
      _storage.read(key: _keyUserName),
      _storage.read(key: _keyUserEmail),
      _storage.read(key: _keyUserRole),
    ]);
    return {
      'id': values[0],
      'name': values[1],
      'email': values[2],
      'role': values[3],
    };
  }

  /// Clear all stored authentication tokens and credentials on logout or 401.
  Future<void> clearAuth() async {
    await Future.wait([
      _storage.delete(key: _keyToken),
      _storage.delete(key: _keyUserId),
      _storage.delete(key: _keyUserName),
      _storage.delete(key: _keyUserEmail),
      _storage.delete(key: _keyUserRole),
    ]);
  }

  /// Check whether an active token is stored.
  Future<bool> hasToken() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }
}
