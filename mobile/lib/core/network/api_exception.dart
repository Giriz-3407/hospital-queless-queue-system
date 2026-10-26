import 'package:dio/dio.dart';

/// Standardized API exception with error fields returned by the backend.
class ApiException implements Exception {
  final String message;
  final String? code;
  final int? statusCode;
  final dynamic details;

  const ApiException({
    required this.message,
    this.code,
    this.statusCode,
    this.details,
  });

  factory ApiException.fromDioException(DioException error) {
    final response = error.response;
    if (response != null && response.data is Map<String, dynamic>) {
      final data = response.data as Map<String, dynamic>;
      final errObj = data['error'];
      if (errObj is Map<String, dynamic>) {
        return ApiException(
          message: errObj['message'] as String? ?? 'An error occurred',
          code: errObj['code'] as String?,
          statusCode: response.statusCode,
          details: errObj['details'],
        );
      }
      if (data['message'] != null) {
        return ApiException(
          message: data['message'] as String,
          statusCode: response.statusCode,
        );
      }
    }

    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return const ApiException(
          message: 'Connection timed out. Please check your network connection and server status.',
          code: 'TIMEOUT',
        );
      case DioExceptionType.connectionError:
        return const ApiException(
          message: 'Unable to connect to the hospital server. Please verify the server is running and accessible.',
          code: 'CONNECTION_ERROR',
        );
      case DioExceptionType.cancel:
        return const ApiException(
          message: 'Request was cancelled.',
          code: 'REQUEST_CANCELLED',
        );
      default:
        return ApiException(
          message: error.message ?? 'An unexpected network error occurred.',
          code: 'UNKNOWN_ERROR',
          statusCode: error.response?.statusCode,
        );
    }
  }

  @override
  String toString() => 'ApiException: [$code] $message (status: $statusCode)';
}
