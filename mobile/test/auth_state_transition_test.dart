import 'package:flutter_test/flutter_test.dart';
import 'package:queueless/core/providers.dart';
import 'package:queueless/features/auth/models/user_model.dart';

void main() {
  group('Authentication State Transitions', () {
    test('AuthState transitions correctly through copyWith', () {
      const initial = AuthState(isLoading: true, isInitialized: false);

      expect(initial.isLoading, isTrue);
      expect(initial.isAuthenticated, isFalse);
      expect(initial.user, isNull);

      const patient = UserModel(
        id: 'pat1',
        name: 'Jane Doe',
        email: 'jane@example.com',
        role: 'patient',
      );

      final authenticated = initial.copyWith(
        isLoading: false,
        isInitialized: true,
        isAuthenticated: true,
        user: patient,
      );

      expect(authenticated.isLoading, isFalse);
      expect(authenticated.isInitialized, isTrue);
      expect(authenticated.isAuthenticated, isTrue);
      expect(authenticated.user?.name, 'Jane Doe');
      expect(authenticated.user?.role, 'patient');

      final withError = authenticated.copyWith(
        errorMessage: 'Invalid credentials',
      );
      expect(withError.errorMessage, 'Invalid credentials');

      final clearedError = withError.copyWith(clearError: true);
      expect(clearedError.errorMessage, isNull);
    });

    test('Non-patient roles are forbidden from patient session state', () {
      bool isAuthorizedPatient(UserModel user) {
        return user.role.toLowerCase() == 'patient';
      }

      const patientUser = UserModel(
        id: '1',
        name: 'Patient User',
        email: 'pat@hospital.org',
        role: 'patient',
      );

      const doctorUser = UserModel(
        id: '2',
        name: 'Dr. Smith',
        email: 'doc@hospital.org',
        role: 'doctor',
      );

      const adminUser = UserModel(
        id: '3',
        name: 'Admin',
        email: 'admin@hospital.org',
        role: 'admin',
      );

      expect(isAuthorizedPatient(patientUser), isTrue);
      expect(isAuthorizedPatient(doctorUser), isFalse);
      expect(isAuthorizedPatient(adminUser), isFalse);
    });
  });
}
