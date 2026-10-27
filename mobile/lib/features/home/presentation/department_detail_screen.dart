import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/loading_indicator.dart';
import '../../../shared/widgets/status_chip.dart';
import '../models/department_model.dart';

class DepartmentDetailScreen extends ConsumerStatefulWidget {
  final String departmentSlug;

  const DepartmentDetailScreen({
    super.key,
    required this.departmentSlug,
  });

  @override
  ConsumerState<DepartmentDetailScreen> createState() => _DepartmentDetailScreenState();
}

class _DepartmentDetailScreenState extends ConsumerState<DepartmentDetailScreen> {
  DepartmentModel? _department;
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _resolveDepartment();
  }

  @override
  void didUpdateWidget(covariant DepartmentDetailScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.departmentSlug != widget.departmentSlug) {
      _resolveDepartment();
    }
  }

  Future<void> _resolveDepartment() async {
    final cleanSlug = widget.departmentSlug.trim();
    if (cleanSlug.isEmpty) {
      setState(() {
        _isLoading = false;
        _errorMessage = 'No department identifier specified in QR link.';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final repo = ref.read(departmentRepositoryProvider);
      final dept = await repo.getDepartmentById(cleanSlug);
      if (mounted) {
        setState(() {
          _department = dept;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = e.toString().replaceFirst('ApiException: ', '');
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    final myQueuesAsync = ref.watch(myQueuesProvider);
    final cleanSlug = widget.departmentSlug.trim();

    void handleBack() {
      if (context.canPop()) {
        context.pop();
      } else if (authState.isAuthenticated) {
        context.go('/home');
      } else {
        context.go('/welcome');
      }
    }

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (didPop) return;
        handleBack();
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text(_department?.name ?? 'Hospital Department'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: handleBack,
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh),
              tooltip: 'Refresh Department',
              onPressed: _resolveDepartment,
            ),
          ],
        ),
        body: SafeArea(
          child: _buildBody(context, authState, myQueuesAsync, cleanSlug),
        ),
      ),
    );
  }

  Widget _buildBody(
    BuildContext context,
    AuthState authState,
    AsyncValue<List<dynamic>> myQueuesAsync,
    String cleanSlug,
  ) {
    if (_isLoading) {
      return const Center(
        child: LoadingIndicator(
          message: 'Resolving clinical department details from hospital server...',
        ),
      );
    }

    if (_errorMessage != null || _department == null) {
      return Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(
                  color: AppTheme.cancelled.withAlpha(25),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.domain_disabled_rounded,
                  size: 40,
                  color: AppTheme.cancelled,
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                'Department Unavailable',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                _errorMessage ??
                    'The department link you scanned could not be found or is no longer active.',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 14,
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 28),
              ElevatedButton.icon(
                icon: const Icon(Icons.local_hospital_outlined, size: 18),
                label: const Text('Browse All Departments'),
                onPressed: () {
                  if (authState.isAuthenticated) {
                    context.go('/departments');
                  } else {
                    context.go('/welcome');
                  }
                },
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: _resolveDepartment,
                child: const Text('Retry Connection'),
              ),
            ],
          ),
        ),
      );
    }

    final dept = _department!;
    final isInactive = !dept.isActive;

    // Active ticket lookup
    final activeTickets = myQueuesAsync.value?.where((t) => t.isActive).toList() ?? [];
    final activeTicket = activeTickets.isNotEmpty ? activeTickets.first : null;

    final redirectPath = '/department/$cleanSlug';

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Department Header Card
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppTheme.border),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withAlpha(8),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryLight,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        '${dept.code} CLINIC',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.primary,
                        ),
                      ),
                    ),
                    if (isInactive)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppTheme.cancelled.withAlpha(25),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text(
                          'Clinic Inactive',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.cancelled,
                          ),
                        ),
                      )
                    else
                      const StatusChip(status: 'WAITING'),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  dept.name,
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textPrimary,
                  ),
                ),
                if (dept.description != null && dept.description!.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    dept.description!,
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppTheme.textSecondary,
                      height: 1.4,
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Live Metrics Grid
          Row(
            children: [
              Expanded(
                child: _buildMetricTile(
                  icon: Icons.timer_outlined,
                  color: AppTheme.primary,
                  label: 'Est. Wait Time',
                  value: dept.estimatedWaitMinutes != null
                      ? '~${dept.estimatedWaitMinutes} min'
                      : 'Unavailable',
                  subtext: 'Live physician pace',
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildMetricTile(
                  icon: Icons.people_outline_rounded,
                  color: AppTheme.waiting,
                  label: 'Patients Waiting',
                  value: '${dept.currentWaiting}',
                  subtext: 'In line ahead',
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _buildMetricTile(
                  icon: Icons.medical_services_outlined,
                  color: AppTheme.completed,
                  label: 'Attending Doctors',
                  value: '${dept.availableDoctorsCount} / ${dept.totalDoctorsCount}',
                  subtext: 'On duty right now',
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildMetricTile(
                  icon: Icons.speed_rounded,
                  color: AppTheme.inConsultation,
                  label: 'Target Consult',
                  value: '${dept.avgConsultationTime} min',
                  subtext: 'Average consultation',
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Inactive Notice
          if (isInactive) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.cancelled.withAlpha(20),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.cancelled, width: 1.5),
              ),
              child: const Row(
                children: [
                  Icon(Icons.warning_amber_rounded, color: AppTheme.cancelled, size: 24),
                  SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'This department is currently closed or inactive. Queue joining is paused. Please speak with hospital reception.',
                      style: TextStyle(
                        fontSize: 13,
                        color: AppTheme.cancelled,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
          ],

          // Authenticated & Active Ticket Restriction Warning
          if (!isInactive && authState.isAuthenticated && activeTicket != null) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.waiting.withAlpha(25),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.waiting, width: 1.5),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.warning_amber_rounded,
                          color: AppTheme.waiting, size: 24),
                      const SizedBox(width: 10),
                      const Expanded(
                        child: Text(
                          'One Active Queue Rule Enforced',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'You already hold an active queue ticket (${activeTicket.tokenNumber}) in ${activeTicket.departmentName}.\n\n'
                    'Hospital policy permits each patient at most ONE active queue entry across all departments.',
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppTheme.textSecondary,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 14),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.accent,
                    ),
                    icon: const Icon(Icons.confirmation_number_outlined, size: 18),
                    label: Text('View Active Ticket (${activeTicket.tokenNumber})'),
                    onPressed: () => context.push('/queue/${activeTicket.id}'),
                  ),
                ],
              ),
            ),
          ],

          // Authenticated & No Active Ticket: Proceed to Join Confirmation
          if (!isInactive && authState.isAuthenticated && activeTicket == null) ...[
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppTheme.primaryLight, width: 1.5),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.check_circle_outline,
                          color: AppTheme.completed, size: 22),
                      const SizedBox(width: 8),
                      Text(
                        'Ready to join ${dept.name}?',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Signed in as ${authState.user?.name ?? 'Patient'}. Tap below to review details and take your turn.',
                    style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.add_task_rounded, size: 18),
                    label: const Text('Confirm & Join Queue'),
                    onPressed: () {
                      context.push(
                        '/queue/join?dept_id=${dept.id}&dept_name=${Uri.encodeComponent(dept.name)}',
                      );
                    },
                  ),
                ],
              ),
            ),
          ],

          // Unauthenticated: Prompt Sign In or Register while preserving redirect
          if (!isInactive && !authState.isAuthenticated) ...[
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppTheme.border),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withAlpha(6),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Join This Department Virtual Queue',
                    style: TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Please sign in or register to take your place in line. Your department selection will be preserved automatically.',
                    style: TextStyle(
                      fontSize: 13,
                      color: AppTheme.textSecondary,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 18),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.login_rounded, size: 18),
                    label: const Text('Sign In to Join Queue'),
                    onPressed: () {
                      context.go('/login?redirect=${Uri.encodeComponent(redirectPath)}');
                    },
                  ),
                  const SizedBox(height: 10),
                  OutlinedButton.icon(
                    icon: const Icon(Icons.person_add_outlined, size: 18),
                    label: const Text('Create Patient Account'),
                    onPressed: () {
                      context.go('/register?redirect=${Uri.encodeComponent(redirectPath)}');
                    },
                  ),
                ],
              ),
            ),
          ],

          const SizedBox(height: 24),
          // Help note
          Center(
            child: Text(
              'Queueless Smart Hospital System &bull; Department QR Routing',
              style: TextStyle(
                fontSize: 11,
                color: AppTheme.textSecondary.withAlpha(150),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricTile({
    required IconData icon,
    required Color color,
    required String label,
    required String value,
    required String subtext,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textSecondary,
                ),
              ),
              Icon(icon, size: 16, color: color),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            value,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            subtext,
            style: TextStyle(
              fontSize: 10,
              color: AppTheme.textSecondary.withAlpha(160),
            ),
          ),
        ],
      ),
    );
  }
}
