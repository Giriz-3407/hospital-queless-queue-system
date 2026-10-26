import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/register_screen.dart';
import '../../features/history/presentation/history_screen.dart';
import '../../features/home/presentation/home_screen.dart';
import '../../features/queue/presentation/join_queue_screen.dart';
import '../../features/queue/presentation/queue_status_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    refreshListenable: _ListenableAdapter(ref),
    redirect: (BuildContext context, GoRouterState state) {
      final authState = ref.read(authNotifierProvider);

      if (authState.isLoading) {
        return null;
      }

      final isAuth = authState.isAuthenticated;
      final location = state.uri.path;
      final isAuthRoute = location == '/login' || location == '/register';

      if (!isAuth && !isAuthRoute) {
        return '/login';
      }

      if (isAuth && (isAuthRoute || location == '/')) {
        return '/home';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const Scaffold(
          body: Center(child: CircularProgressIndicator()),
        ),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/home',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/queue/join',
        builder: (context, state) {
          final deptId = state.uri.queryParameters['dept_id'];
          final deptName = state.uri.queryParameters['dept_name'];
          return JoinQueueScreen(
            initialDeptId: deptId,
            initialDeptName: deptName,
          );
        },
      ),
      GoRoute(
        path: '/queue/:id',
        builder: (context, state) {
          final id = state.pathParameters['id'] ?? '';
          return QueueStatusScreen(queueId: id);
        },
      ),
      GoRoute(
        path: '/history',
        builder: (context, state) => const HistoryScreen(),
      ),
    ],
  );
});

class _ListenableAdapter extends ChangeNotifier {
  _ListenableAdapter(Ref ref) {
    ref.listen(authNotifierProvider, (_, _) => notifyListeners());
  }
}
