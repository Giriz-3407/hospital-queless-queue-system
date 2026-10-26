import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'network/api_client.dart';
import 'storage/secure_storage_service.dart';
import '../features/auth/models/user_model.dart';
import '../features/auth/repositories/auth_repository.dart';
import '../features/home/models/department_model.dart';
import '../features/home/repositories/department_repository.dart';
import '../features/queue/models/queue_ticket_model.dart';
import '../features/queue/repositories/queue_repository.dart';

// Storage & Network
final secureStorageProvider = Provider<SecureStorageService>((ref) {
  return SecureStorageService();
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(secureStorageProvider);
  return ApiClient(storage: storage);
});

// Repositories
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  final storage = ref.watch(secureStorageProvider);
  return AuthRepository(client: client, storage: storage);
});

final departmentRepositoryProvider = Provider<DepartmentRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  return DepartmentRepository(client: client);
});

final queueRepositoryProvider = Provider<QueueRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  return QueueRepository(client: client);
});

// Auth State
class AuthState {
  final bool isLoading;
  final bool isAuthenticated;
  final UserModel? user;
  final String? errorMessage;

  const AuthState({
    this.isLoading = false,
    this.isAuthenticated = false,
    this.user,
    this.errorMessage,
  });

  AuthState copyWith({
    bool? isLoading,
    bool? isAuthenticated,
    UserModel? user,
    String? errorMessage,
    bool clearError = false,
  }) {
    return AuthState(
      isLoading: isLoading ?? this.isLoading,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      user: user ?? this.user,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    Future.microtask(() => checkInitialAuth());
    return const AuthState(isLoading: true);
  }

  AuthRepository get _repo => ref.read(authRepositoryProvider);

  Future<void> checkInitialAuth() async {
    try {
      final isAuth = await _repo.isAuthenticated();
      if (isAuth) {
        final user = await _repo.getMe();
        state = AuthState(isAuthenticated: true, user: user);
      } else {
        state = const AuthState(isAuthenticated: false);
      }
    } catch (_) {
      state = const AuthState(isAuthenticated: false);
    }
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final authData = await _repo.login(email: email, password: password);
      state = AuthState(isAuthenticated: true, user: authData.user);
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString().replaceFirst('ApiException: ', ''),
      );
      return false;
    }
  }

  Future<bool> register({
    required String name,
    required String email,
    required String password,
    String? phone,
  }) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final authData = await _repo.register(
        name: name,
        email: email,
        password: password,
        phone: phone,
      );
      state = AuthState(isAuthenticated: true, user: authData.user);
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString().replaceFirst('ApiException: ', ''),
      );
      return false;
    }
  }

  Future<void> logout() async {
    await _repo.logout();
    state = const AuthState(isAuthenticated: false);
  }

  void handleSessionExpired() {
    state = const AuthState(
      isAuthenticated: false,
      errorMessage: 'Your session has expired. Please log in again.',
    );
  }
}

final authNotifierProvider =
    NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

// Department & Queue Providers
final departmentsProvider =
    FutureProvider.autoDispose<List<DepartmentModel>>((ref) async {
  final repo = ref.watch(departmentRepositoryProvider);
  return repo.getDepartments();
});

final myQueuesProvider =
    FutureProvider.autoDispose<List<QueueTicketModel>>((ref) async {
  final repo = ref.watch(queueRepositoryProvider);
  return repo.getMyQueues();
});

final patientHistoryProvider =
    FutureProvider.autoDispose<List<QueueTicketModel>>((ref) async {
  final repo = ref.watch(queueRepositoryProvider);
  return repo.getPatientQueueHistory();
});
