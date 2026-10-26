import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/loading_indicator.dart';
import '../../queue/models/queue_ticket_model.dart';
import '../models/department_model.dart';

/// Screen listing all available hospital departments with real-time wait times
/// and physician availability. Enforces single active queue per patient across hospital.
class DepartmentsScreen extends ConsumerStatefulWidget {
  const DepartmentsScreen({super.key});

  @override
  ConsumerState<DepartmentsScreen> createState() => _DepartmentsScreenState();
}

class _DepartmentsScreenState extends ConsumerState<DepartmentsScreen> {
  final _searchController = TextEditingController();
  String _searchQuery = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final departmentsAsync = ref.watch(departmentsProvider);
    final myQueuesAsync = ref.watch(myQueuesProvider);

    final activeTickets =
        myQueuesAsync.value?.where((t) => t.isActive).toList() ?? [];
    final activeTicket = activeTickets.isNotEmpty ? activeTickets.first : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Clinical Departments'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh Departments',
            onPressed: () {
              ref.invalidate(departmentsProvider);
              ref.invalidate(myQueuesProvider);
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Single Active Queue Policy Alert Banner (if active ticket exists)
          if (activeTicket != null)
            Container(
              margin: const EdgeInsets.fromLTRB(16, 12, 16, 4),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.waiting.withAlpha(25),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.waiting),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline,
                      color: AppTheme.waiting, size: 22),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Active Ticket: ${activeTicket.tokenNumber} (${activeTicket.departmentName})',
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'Hospital policy limits patients to 1 active queue at a time.',
                          style: TextStyle(
                            fontSize: 11,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  TextButton(
                    onPressed: () => context.go('/queue/${activeTicket.id}'),
                    child: const Text('Track', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
            ),

          // Search Bar
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 8),
            child: TextField(
              controller: _searchController,
              onChanged: (val) =>
                  setState(() => _searchQuery = val.trim().toLowerCase()),
              decoration: InputDecoration(
                hintText: 'Search department or specialty...',
                prefixIcon:
                    const Icon(Icons.search, color: AppTheme.textSecondary),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear, size: 20),
                        onPressed: () {
                          _searchController.clear();
                          setState(() => _searchQuery = '');
                        },
                      )
                    : null,
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
            ),
          ),

          // Department List
          Expanded(
            child: departmentsAsync.when(
              data: (departments) {
                final filtered = departments.where((d) {
                  if (!d.isActive) return false;
                  if (_searchQuery.isEmpty) return true;
                  return d.name.toLowerCase().contains(_searchQuery) ||
                      d.code.toLowerCase().contains(_searchQuery) ||
                      (d.description != null &&
                          d.description!.toLowerCase().contains(_searchQuery));
                }).toList();

                if (filtered.isEmpty) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.search_off_rounded,
                            size: 48,
                            color: AppTheme.textSecondary,
                          ),
                          const SizedBox(height: 12),
                          Text(
                            _searchQuery.isEmpty
                                ? 'No active clinical departments available.'
                                : 'No departments match "$_searchQuery"',
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 15,
                              color: AppTheme.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }

                return RefreshIndicator(
                  onRefresh: () async {
                    ref.invalidate(departmentsProvider);
                    ref.invalidate(myQueuesProvider);
                  },
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: filtered.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 14),
                    itemBuilder: (ctx, i) => _DepartmentCard(
                      department: filtered[i],
                      activeTicket: activeTicket,
                    ),
                  ),
                );
              },
              loading: () => const LoadingIndicator(
                message: 'Loading hospital departments...',
              ),
              error: (err, _) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.error_outline,
                          color: AppTheme.error, size: 40),
                      const SizedBox(height: 12),
                      Text(
                        'Unable to load clinical departments:\n$err',
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: AppTheme.error,
                          fontSize: 13,
                        ),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        icon: const Icon(Icons.refresh),
                        label: const Text('Retry'),
                        onPressed: () => ref.invalidate(departmentsProvider),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DepartmentCard extends StatelessWidget {
  final DepartmentModel department;
  final QueueTicketModel? activeTicket;

  const _DepartmentCard({
    required this.department,
    this.activeTicket,
  });

  void _handleJoinTapped(BuildContext context) {
    if (activeTicket != null) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: AppTheme.waiting),
              SizedBox(width: 10),
              Expanded(
                child: Text('Active Queue Policy'),
              ),
            ],
          ),
          content: Text(
            'You already hold an active queue ticket (${activeTicket!.tokenNumber}) in ${activeTicket!.departmentName}.\n\n'
            'Each patient may have at most one active queue ticket across the entire hospital at any time. '
            'Would you like to open your active ticket tracker instead?',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Close'),
            ),
            ElevatedButton.icon(
              icon: const Icon(Icons.confirmation_number_outlined, size: 18),
              label: const Text('View Active Ticket'),
              onPressed: () {
                Navigator.pop(ctx);
                context.go('/queue/${activeTicket!.id}');
              },
            ),
          ],
        ),
      );
      return;
    }

    context.go(
      '/queue/join?dept_id=${department.id}&dept_name=${Uri.encodeComponent(department.name)}',
    );
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Department Icon Badge
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryLight,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: const Icon(
                    Icons.local_hospital_rounded,
                    color: AppTheme.primary,
                    size: 26,
                  ),
                ),
                const SizedBox(width: 14),
                // Title and Code
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        department.name,
                        style: const TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: AppTheme.border,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          'CODE: ${department.code}',
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.5,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (department.description != null &&
                department.description!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                department.description!,
                style: const TextStyle(
                  fontSize: 13,
                  color: AppTheme.textSecondary,
                  height: 1.35,
                ),
              ),
            ],
            const SizedBox(height: 16),
            const Divider(height: 1, color: AppTheme.border),
            const SizedBox(height: 14),

            // Live Metrics Row
            Row(
              children: [
                // Waiting
                Expanded(
                  child: _MetricBadge(
                    icon: Icons.people_outline,
                    label: 'Waiting',
                    value: '${department.currentWaiting} patients',
                    color: AppTheme.accent,
                  ),
                ),
                // Est wait
                Expanded(
                  child: _MetricBadge(
                    icon: Icons.access_time_rounded,
                    label: 'Est. Wait',
                    value: department.estimatedWaitMinutes != null
                        ? '~${department.estimatedWaitMinutes} min'
                        : 'Unavailable',
                    color: AppTheme.waiting,
                  ),
                ),
                // Doctors
                Expanded(
                  child: _MetricBadge(
                    icon: Icons.medical_services_outlined,
                    label: 'On Duty',
                    value: department.availableDoctorsCount > 0
                        ? '${department.availableDoctorsCount} doctor${department.availableDoctorsCount > 1 ? "s" : ""}'
                        : '0 available',
                    color: department.availableDoctorsCount > 0
                        ? AppTheme.completed
                        : AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Join Queue Action
            ElevatedButton.icon(
              icon: Icon(activeTicket != null
                  ? Icons.info_outline
                  : Icons.add_circle_outline,
                  size: 20),
              label: Text(activeTicket != null
                  ? 'Join Queue (Active Ticket Exists)'
                  : 'Join This Queue'),
              style: activeTicket != null
                  ? ElevatedButton.styleFrom(backgroundColor: AppTheme.textSecondary)
                  : null,
              onPressed: () => _handleJoinTapped(context),
            ),
          ],
        ),
      ),
    );
  }
}

class _MetricBadge extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _MetricBadge({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 14, color: AppTheme.textSecondary),
            const SizedBox(width: 4),
            Expanded(
              child: Text(
                label,
                style: const TextStyle(
                  fontSize: 11,
                  color: AppTheme.textSecondary,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w700,
            color: color,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ],
    );
  }
}
