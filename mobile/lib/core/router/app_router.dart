import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers.dart';
import '../../features/auth/presentation/splash_screen.dart';
import '../../features/auth/presentation/welcome_screen.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/register_screen.dart';
import '../../features/history/presentation/history_screen.dart';
import '../../features/home/presentation/department_detail_screen.dart';
import '../../features/home/presentation/departments_screen.dart';
import '../../features/home/presentation/home_screen.dart';
import '../../features/home/presentation/main_shell.dart';
import '../../features/patient/presentation/profile_screen.dart';
import '../../features/queue/presentation/active_queue_tab.dart';
import '../../features/queue/presentation/join_queue_screen.dart';
import '../../features/queue/presentation/queue_status_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    refreshListenable: _ListenableAdapter(ref),
    redirect: (BuildContext context, GoRouterState state) {
      final authState = ref.read(authNotifierProvider);

      // Still running startup checks
      if (!authState.isInitialized) {
        return null;
      }

      final isAuth = authState.isAuthenticated;
      final location = state.uri.path;
      final isDepartmentRoute = location.startsWith('/department') || location.startsWith('/anything/department');
      final isPublicRoute = location == '/' ||
          location == '/welcome' ||
          location == '/login' ||
          location == '/register' ||
          isDepartmentRoute;

      // Unauthenticated user trying to access protected screen
      if (!isAuth && !isPublicRoute) {
        return '/welcome';
      }

      // Authenticated user trying to access public auth screens
      if (isAuth && (location == '/' || location == '/welcome' || location == '/login' || location == '/register')) {
        final redirectParam = state.uri.queryParameters['redirect'];
        if (redirectParam != null && redirectParam.isNotEmpty && redirectParam != '/login' && redirectParam != '/register') {
          return redirectParam;
        }
        return '/home';
      }

      return null;
    },
    routes: [
      // Splash Startup
      GoRoute(
        path: '/',
        builder: (context, state) => const SplashScreen(),
      ),
      // Public Auth Routes
      GoRoute(
        path: '/welcome',
        builder: (context, state) => const WelcomeScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),

      // Department QR Route Handlers (Standard and Test Redirect URLs)
      GoRoute(
        path: '/department/:slug',
        builder: (context, state) {
          final slug = state.pathParameters['slug'] ?? '';
          return DepartmentDetailScreen(departmentSlug: slug);
        },
      ),
      GoRoute(
        path: '/anything/department/:slug',
        builder: (context, state) {
          final slug = state.pathParameters['slug'] ?? '';
          return DepartmentDetailScreen(departmentSlug: slug);
        },
      ),

      // Standalone Fullscreen Flow Routes
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

      // Authenticated Shell with Persistent Bottom Navigation Bar
      ShellRoute(
        builder: (context, state, child) {
          return MainShell(child: child);
        },
        routes: [
          GoRoute(
            path: '/home',
            builder: (context, state) => const HomeScreen(),
          ),
          GoRoute(
            path: '/departments',
            builder: (context, state) => const DepartmentsScreen(),
          ),
          GoRoute(
            path: '/queue',
            builder: (context, state) => const ActiveQueueTab(),
          ),
          GoRoute(
            path: '/history',
            builder: (context, state) => const HistoryScreen(),
          ),
          GoRoute(
            path: '/profile',
            builder: (context, state) => const ProfileScreen(),
          ),
        ],
      ),
    ],
  );
});

class _ListenableAdapter extends ChangeNotifier {
  _ListenableAdapter(Ref ref) {
    ref.listen(authNotifierProvider, (_, _) => notifyListeners());
  }
}
