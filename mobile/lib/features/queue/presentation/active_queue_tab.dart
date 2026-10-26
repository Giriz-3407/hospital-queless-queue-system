import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/loading_indicator.dart';
import 'queue_status_screen.dart';

/// The active queue tab in the bottom navigation bar.
/// If the patient currently holds an active ticket, shows live queue tracking;
/// otherwise, shows a helpful empty state guiding the patient to select a department.
class ActiveQueueTab extends ConsumerWidget {
  const ActiveQueueTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final myQueuesAsync = ref.watch(myQueuesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Active Queue'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh Queue',
            onPressed: () => ref.invalidate(myQueuesProvider),
          ),
        ],
      ),
      body: myQueuesAsync.when(
        data: (tickets) {
          final activeTickets = tickets.where((t) => t.isActive).toList();

          if (activeTickets.isEmpty) {
            return Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryLight,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.confirmation_number_outlined,
                        size: 56,
                        color: AppTheme.primary,
                      ),
                    ),
                    const SizedBox(height: 24),
                    const Text(
                      'No Active Queue Ticket',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'You do not currently hold an active hospital queue ticket.\nSelect a department to take a number virtually.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 14,
                        color: AppTheme.textSecondary,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 28),
                    ElevatedButton.icon(
                      icon: const Icon(Icons.add_circle_outline),
                      label: const Text('Browse Departments & Join Queue'),
                      onPressed: () => context.go('/departments'),
                    ),
                  ],
                ),
              ),
            );
          }

          // If there is an active ticket, show the tracking screen for it
          final primaryTicket = activeTickets.first;
          return QueueStatusScreen(queueId: primaryTicket.id);
        },
        loading: () => const LoadingIndicator(
          message: 'Checking active queue tickets...',
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
                  'Error fetching queue status:\n$err',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppTheme.error),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => ref.invalidate(myQueuesProvider),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
