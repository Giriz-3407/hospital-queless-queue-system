import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/loading_indicator.dart';
import '../../../shared/widgets/status_chip.dart';
import '../../home/models/department_model.dart';
import '../../queue/models/queue_ticket_model.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authNotifierProvider);
    final departmentsAsync = ref.watch(departmentsProvider);
    final myQueuesAsync = ref.watch(myQueuesProvider);
    final summaryAsync = ref.watch(patientSummaryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Queueless Hospital'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh Dashboard',
            onPressed: () {
              ref.invalidate(departmentsProvider);
              ref.invalidate(myQueuesProvider);
              ref.invalidate(patientSummaryProvider);
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(departmentsProvider);
          ref.invalidate(myQueuesProvider);
          ref.invalidate(patientSummaryProvider);
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Welcome Greeting Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryLight,
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: const Icon(
                          Icons.local_hospital_rounded,
                          color: AppTheme.primary,
                          size: 28,
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Hello, ${authState.user?.name ?? "Patient"}',
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: AppTheme.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 2),
                            const Text(
                              'Queueless Smart Virtual Queuing',
                              style: TextStyle(
                                fontSize: 13,
                                color: AppTheme.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.account_circle_outlined,
                            size: 28, color: AppTheme.primary),
                        tooltip: 'View Profile',
                        onPressed: () => context.go('/profile'),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Overview Stats Row (from patientSummaryProvider)
              summaryAsync.when(
                data: (summary) => Row(
                  children: [
                    Expanded(
                      child: _SummaryCard(
                        title: 'Active Tickets',
                        count: '${summary.activeTicketsCount}',
                        color: AppTheme.accent,
                        icon: Icons.confirmation_number_outlined,
                        onTap: () => context.go('/queue'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _SummaryCard(
                        title: 'Completed Visits',
                        count: '${summary.pastVisitsCount}',
                        color: AppTheme.completed,
                        icon: Icons.done_all_rounded,
                        onTap: () => context.go('/history'),
                      ),
                    ),
                  ],
                ),
                loading: () => const SizedBox.shrink(),
                error: (_, _) => const SizedBox.shrink(),
              ),
              const SizedBox(height: 20),

              // Active Queue Card or Encouraging Empty State
              myQueuesAsync.when(
                data: (tickets) {
                  final active = tickets.where((t) => t.isActive).toList();
                  if (active.isNotEmpty) {
                    final ticket = active.first;
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'Your Active Queue Ticket',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: AppTheme.textPrimary,
                              ),
                            ),
                            TextButton.icon(
                              icon: const Icon(Icons.arrow_forward, size: 16),
                              label: const Text('Track Full View'),
                              onPressed: () =>
                                  context.go('/queue/${ticket.id}'),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        _ActiveTicketBanner(ticket: ticket),
                        const SizedBox(height: 24),
                      ],
                    );
                  } else {
                    return Card(
                      color: AppTheme.primaryLight.withAlpha(40),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                        side: BorderSide(
                          color: AppTheme.primary.withAlpha(50),
                        ),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(18),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.info_outline,
                                    color: AppTheme.primary, size: 20),
                                SizedBox(width: 8),
                                Text(
                                  'No Active Queue Ticket',
                                  style: TextStyle(
                                    fontSize: 15,
                                    fontWeight: FontWeight.bold,
                                    color: AppTheme.primaryDark,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            const Text(
                              'You are not currently waiting in line. Choose a clinical department below to take a queue token virtually.',
                              style: TextStyle(
                                fontSize: 13,
                                color: AppTheme.textSecondary,
                                height: 1.35,
                              ),
                            ),
                            const SizedBox(height: 14),
                            ElevatedButton.icon(
                              icon: const Icon(Icons.add_circle_outline,
                                  size: 18),
                              label: const Text('Browse Departments & Join'),
                              onPressed: () => context.go('/departments'),
                            ),
                          ],
                        ),
                      ),
                    );
                  }
                },
                loading: () => const Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: Center(child: CircularProgressIndicator()),
                ),
                error: (_, _) => const SizedBox.shrink(),
              ),
              const SizedBox(height: 24),

              // Clinical Departments Section
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Hospital Departments',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  TextButton(
                    onPressed: () => context.go('/departments'),
                    child: const Text('View All'),
                  ),
                ],
              ),
              const SizedBox(height: 10),

              // Department Cards
              departmentsAsync.when(
                data: (depts) {
                  final active = depts.where((d) => d.isActive).take(4).toList();
                  final activeTickets =
                      myQueuesAsync.value?.where((t) => t.isActive).toList() ?? [];
                  final activeTicket =
                      activeTickets.isNotEmpty ? activeTickets.first : null;

                  if (active.isEmpty) {
                    return const Center(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Text(
                          'No hospital departments available.',
                          style: TextStyle(color: AppTheme.textSecondary),
                        ),
                      ),
                    );
                  }
                  return ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: active.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 12),
                    itemBuilder: (ctx, i) => _DepartmentTile(
                      department: active[i],
                      activeTicket: activeTicket,
                    ),
                  );
                },
                loading: () => const LoadingIndicator(
                  message: 'Loading clinical departments...',
                ),
                error: (err, _) => Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      children: [
                        const Icon(Icons.error_outline,
                            color: AppTheme.error, size: 36),
                        const SizedBox(height: 8),
                        Text(
                          'Error loading departments:\n$err',
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                              color: AppTheme.error, fontSize: 13),
                        ),
                        const SizedBox(height: 12),
                        OutlinedButton(
                          onPressed: () => ref.invalidate(departmentsProvider),
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  final String title;
  final String count;
  final Color color;
  final IconData icon;
  final VoidCallback onTap;

  const _SummaryCard({
    required this.title,
    required this.count,
    required this.color,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: color.withAlpha(25),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: color, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      count,
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w900,
                        color: color,
                      ),
                    ),
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ActiveTicketBanner extends StatelessWidget {
  final QueueTicketModel ticket;

  const _ActiveTicketBanner({required this.ticket});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppTheme.primary, width: 1.5),
        ),
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      ticket.departmentName,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    Text(
                      'Department Code: ${ticket.departmentCode}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ],
                ),
                StatusChip(status: ticket.status),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'TOKEN NUMBER',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.8,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      ticket.tokenNumber,
                      style: const TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w900,
                        color: AppTheme.primaryDark,
                      ),
                    ),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      'Position #${ticket.livePosition}',
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.accent,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${ticket.patientsAhead} patients ahead',
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    Text(
                      ticket.liveEstimatedWaitMinutes != null
                          ? '~${ticket.liveEstimatedWaitMinutes} min wait'
                          : 'Wait time unavailable',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.waiting,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 14),
            ElevatedButton.icon(
              icon: const Icon(Icons.visibility_outlined, size: 18),
              label: const Text('Open Live Tracker & Details'),
              onPressed: () => context.go('/queue/${ticket.id}'),
            ),
          ],
        ),
      ),
    );
  }
}

class _DepartmentTile extends StatelessWidget {
  final DepartmentModel department;
  final QueueTicketModel? activeTicket;

  const _DepartmentTile({
    required this.department,
    this.activeTicket,
  });

  void _onJoinPressed(BuildContext context) {
    if (activeTicket != null) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: AppTheme.waiting),
              SizedBox(width: 8),
              Text('Single Active Queue Policy'),
            ],
          ),
          content: Text(
            'You already hold active queue ticket ${activeTicket!.tokenNumber} in ${activeTicket!.departmentName}.\n\n'
            'Hospital policy allows at most one active queue ticket across the hospital at any given time. '
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
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryLight,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(
                    Icons.local_hospital_rounded,
                    color: AppTheme.primary,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        department.name,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      Text(
                        'Code: ${department.code}',
                        style: const TextStyle(
                          fontSize: 11,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size(90, 36),
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                  ),
                  onPressed: () => _onJoinPressed(context),
                  child: Text(
                    activeTicket != null ? 'Active' : 'Join',
                    style: TextStyle(
                      fontSize: 13,
                      color: activeTicket != null
                          ? AppTheme.textSecondary
                          : AppTheme.primary,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Text(
                  'Waiting: ${department.currentWaiting} patients',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppTheme.textSecondary,
                  ),
                ),
                const Spacer(),
                Text(
                  department.estimatedWaitMinutes != null
                      ? 'Est. Wait: ~${department.estimatedWaitMinutes} min'
                      : 'Wait: unavailable',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.waiting,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
