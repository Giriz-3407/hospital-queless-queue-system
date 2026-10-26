import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Authentication Input Validation Tests', () {
    test('Email format validation accepts standard and normalized emails', () {
      final emailRegex = RegExp(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$');

      expect(emailRegex.hasMatch('patient@hospital.org'), isTrue);
      expect(emailRegex.hasMatch('jane.doe+test@gmail.com'), isTrue);
      expect(emailRegex.hasMatch('patient123@sub.domain.co'), isTrue);

      expect(emailRegex.hasMatch(''), isFalse);
      expect(emailRegex.hasMatch('invalid-email'), isFalse);
      expect(emailRegex.hasMatch('@missingusername.com'), isFalse);
      expect(emailRegex.hasMatch('patient@missingtld'), isFalse);
      expect(emailRegex.hasMatch('patient with spaces@hospital.org'), isFalse);
    });

    test('Password complexity enforces minimum 8 characters', () {
      bool isPasswordValid(String? val) => val != null && val.length >= 8;

      expect(isPasswordValid(''), isFalse);
      expect(isPasswordValid('1234567'), isFalse);
      expect(isPasswordValid('short'), isFalse);
      expect(isPasswordValid('Password123!'), isTrue);
      expect(isPasswordValid('12345678'), isTrue);
    });

    test('Password confirmation matches primary password exactly', () {
      bool passwordsMatch(String p1, String p2) => p1 == p2;

      expect(passwordsMatch('Secret123!', 'Secret123!'), isTrue);
      expect(passwordsMatch('Secret123!', 'Secret123'), isFalse);
      expect(passwordsMatch('Secret123!', 'secret123!'), isFalse);
    });

    test('Phone number validation allows international/local formats when provided', () {
      final phoneRegex = RegExp(r'^[+0-9\s-]{7,20}$');

      expect(phoneRegex.hasMatch('+1-555-0199'), isTrue);
      expect(phoneRegex.hasMatch('+91 9876543210'), isTrue);
      expect(phoneRegex.hasMatch('555-0199'), isTrue);
      expect(phoneRegex.hasMatch('9876543210'), isTrue);

      expect(phoneRegex.hasMatch('12345'), isFalse); // under 7 chars
      expect(phoneRegex.hasMatch('invalid-abc-phone'), isFalse);
    });

    test('Public registration strictly enforces patient role', () {
      String sanitizeRole(String? role) {
        if (role == null || role.toLowerCase() == 'patient' || role.isEmpty) {
          return 'patient';
        }
        throw ArgumentError('Public registration restricted to patient');
      }

      expect(sanitizeRole(null), 'patient');
      expect(sanitizeRole('patient'), 'patient');
      expect(sanitizeRole('PATIENT'), 'patient');
      expect(() => sanitizeRole('doctor'), throwsArgumentError);
      expect(() => sanitizeRole('admin'), throwsArgumentError);
    });
  });
}
