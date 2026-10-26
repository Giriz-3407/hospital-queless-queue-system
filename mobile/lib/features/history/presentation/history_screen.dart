import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/loading_indicator.dart';
import '../../../shared/widgets/status_chip.dart';
import '../../queue/models/queue_ticket_model.dart';

class HistoryScreen extends ConsumerStatefulWidget {
  const HistoryScreen({super.key});

  @override
  ConsumerState<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends ConsumerState<HistoryScreen> {
  String _statusFilter = 'ALL';

  void _showConsultationSummaryModal(
      BuildContext context, QueueTicketModel ticket) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return Padding(
          padding: EdgeInsets.fromLTRB(
              20, 20, 20, MediaQuery.of(ctx).viewInsets.bottom + 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppTheme.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Consultation Summary',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  StatusChip(status: ticket.status),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                'Department: ${ticket.departmentName} (${ticket.departmentCode})',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textSecondary,
                ),
              ),
              Text(
                'Token: ${ticket.tokenNumber}',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.primaryDark,
                ),
              ),
              const SizedBox(height: 16),
              const Divider(color: AppTheme.border),
              const SizedBox(height: 12),

              // Visit details
              _SummaryDetailRow(
                label: 'Visit Date',
                value: ticket.queueDate ??
                    (ticket.joinedAt != null
                        ? ticket.joinedAt!.split('T').first
                        : '--'),
              ),
              const SizedBox(height: 8),
              if (ticket.doctorName != null) ...[
                _SummaryDetailRow(
                  label: 'Attending Physician',
                  value: ticket.doctorName!,
                ),
                const SizedBox(height: 8),
              ],
              if (ticket.reason != null && ticket.reason!.isNotEmpty) ...[
                _SummaryDetailRow(
                  label: 'Reason for Visit',
                  value: ticket.reason!,
                ),
                const SizedBox(height: 8),
              ],
              _SummaryDetailRow(
                label: 'Status',
                value: ticket.status,
              ),
              const SizedBox(height: 16),

              // Patient Summary Release Notice (Section 5)
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.primaryLight.withAlpha(80),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.primary.withAlpha(50)),
                ),
                child: const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: EdgeInsets.only(top: 2),
                      child: Icon(Icons.info_outline,
                          size: 20, color: AppTheme.primary),
                    ),
                    SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Patient Clinical Summary Release',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.primaryDark,
                            ),
                          ),
                          SizedBox(height: 4),
                          Text(
                            'Under hospital medical records policy, clinical consultation summaries are made viewable once formally signed and authorized for patient release by your attending doctor. Internal clinical notes remain restricted.',
                            style: TextStyle(
                              fontSize: 12,
                              color: AppTheme.textSecondary,
                              height: 1.35,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Close'),
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final historyAsync = ref.watch(patientHistoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Queue History'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh History',
            onPressed: () => ref.invalidate(patientHistoryProvider),
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter Chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                _buildFilterChip('ALL', 'All Visits'),
                const SizedBox(width: 8),
                _buildFilterChip('COMPLETED', 'Completed'),
                const SizedBox(width: 8),
                _buildFilterChip('WAITING', 'Waiting'),
                const SizedBox(width: 8),
                _buildFilterChip('CANCELLED', 'Cancelled'),
                const SizedBox(width: 8),
                _buildFilterChip('NO_SHOW', 'No-Show'),
              ],
            ),
          ),
          const Divider(height: 1, color: AppTheme.border),

          // Tickets List
          Expanded(
            child: historyAsync.when(
              data: (tickets) {
                final filtered = tickets.where((t) {
                  if (_statusFilter == 'ALL') return true;
                  return t.status.toUpperCase() == _statusFilter;
                }).toList();

                if (filtered.isEmpty) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.history_toggle_off_rounded,
                            size: 48,
                            color: AppTheme.textSecondary,
                          ),
                          const SizedBox(height: 12),
                          Text(
                            _statusFilter == 'ALL'
                                ? 'No hospital visit history found.'
                                : 'No visits with status "$_statusFilter"',
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'When you take virtual queue numbers, your complete history will appear here.',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 13,
                              color: AppTheme.textSecondary,
                            ),
                          ),
                          const SizedBox(height: 20),
                          ElevatedButton(
                            onPressed: () => context.go('/departments'),
                            child: const Text('Browse Departments'),
                          ),
                        ],
                      ),
                    ),
                  );
                }

                return RefreshIndicator(
                  onRefresh: () async => ref.invalidate(patientHistoryProvider),
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: filtered.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 12),
                    itemBuilder: (ctx, i) {
                      final ticket = filtered[i];
                      return _HistoryTicketCard(
                        ticket: ticket,
                        onViewSummary: () =>
                            _showConsultationSummaryModal(context, ticket),
                      );
                    },
                  ),
                );
              },
              loading: () => const LoadingIndicator(
                message: 'Loading visit history...',
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
                        'Error loading history:\n$err',
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: AppTheme.error),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () => ref.invalidate(patientHistoryProvider),
                        child: const Text('Retry'),
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

  Widget _buildFilterChip(String value, String label) {
    final isSelected = _statusFilter == value;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        if (selected) {
          setState(() => _statusFilter = value);
        }
      },
      selectedColor: AppTheme.primaryLight,
      labelStyle: TextStyle(
        fontSize: 12,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        color: isSelected ? AppTheme.primaryDark : AppTheme.textSecondary,
      ),
    );
  }
}

class _HistoryTicketCard extends StatelessWidget {
  final QueueTicketModel ticket;
  final VoidCallback onViewSummary;

  const _HistoryTicketCard({
    required this.ticket,
    required this.onViewSummary,
  });

  String _formatDate(String? isoString) {
    if (isoString == null || isoString.isEmpty) return '--';
    try {
      final dt = DateTime.parse(isoString).toLocal();
      return DateFormat('MMM dd, yyyy • hh:mm a').format(dt);
    } catch (_) {
      return isoString;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDone = ticket.isCompleted;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
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
                      'Code: ${ticket.departmentCode}',
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
            const SizedBox(height: 12),
            Row(
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryLight,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    ticket.tokenNumber,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w900,
                      color: AppTheme.primaryDark,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    _formatDate(ticket.joinedAt ?? ticket.createdAt),
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ),
              ],
            ),
            if (ticket.doctorName != null) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.medical_services_outlined,
                      size: 14, color: AppTheme.textSecondary),
                  const SizedBox(width: 6),
                  Text(
                    'Doctor: ${ticket.doctorName}',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                ],
              ),
            ],
            if (ticket.reason != null && ticket.reason!.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                'Reason: ${ticket.reason}',
                style: const TextStyle(
                  fontSize: 12,
                  fontStyle: FontStyle.italic,
                  color: AppTheme.textSecondary,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                if (ticket.isActive) ...[
                  TextButton.icon(
                    icon: const Icon(Icons.arrow_forward_rounded, size: 16),
                    label: const Text('Track Live'),
                    onPressed: () => context.go('/queue/${ticket.id}'),
                  ),
                ] else if (isDone) ...[
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size(120, 36),
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                    ),
                    icon: const Icon(Icons.receipt_long_outlined, size: 16),
                    label: const Text('Visit Summary',
                        style: TextStyle(fontSize: 12)),
                    onPressed: onViewSummary,
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryDetailRow extends StatelessWidget {
  final String label;
  final String value;

  const _SummaryDetailRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 130,
          child: Text(
            label,
            style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: AppTheme.textPrimary,
            ),
          ),
        ),
      ],
    );
  }
}
