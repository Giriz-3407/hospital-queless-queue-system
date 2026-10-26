import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/config/api_config.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/server_settings_dialog.dart';

/// Screen presenting the authenticated patient's account profile, hospital visit
/// overview, server configuration shortcut, and secure sign-out.
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  Future<void> _logout(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Sign Out'),
        content: const Text(
          'Are you sure you want to sign out from your Queueless account on this device?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.error,
              foregroundColor: Colors.white,
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Sign Out'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      // Invalidate all patient cached data
      ref.invalidate(myQueuesProvider);
      ref.invalidate(patientSummaryProvider);
      ref.invalidate(patientHistoryProvider);
      ref.invalidate(departmentsProvider);

      await ref.read(authNotifierProvider.notifier).logout();
      if (context.mounted) {
        context.go('/welcome');
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authNotifierProvider);
    final user = authState.user;
    final summaryAsync = ref.watch(patientSummaryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Patient Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'Server Settings',
            onPressed: () => ServerSettingsDialog.show(context),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Avatar & Name Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    CircleAvatar(
                      radius: 40,
                      backgroundColor: AppTheme.primaryLight,
                      child: Text(
                        (user?.name != null && user!.name.isNotEmpty)
                            ? user.name[0].toUpperCase()
                            : 'P',
                        style: const TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.w900,
                          color: AppTheme.primaryDark,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      user?.name ?? 'Patient',
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      user?.email ?? '',
                      style: const TextStyle(
                        fontSize: 14,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryLight,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Text(
                        'Verified Patient Account',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.primaryDark,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Statistics Summary Card
            summaryAsync.when(
              data: (summary) => Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _StatColumn(
                        label: 'Active Tickets',
                        value: '${summary.activeTicketsCount}',
                        color: AppTheme.accent,
                      ),
                      const SizedBox(
                        height: 36,
                        child: VerticalDivider(color: AppTheme.border),
                      ),
                      _StatColumn(
                        label: 'Past Visits',
                        value: '${summary.pastVisitsCount}',
                        color: AppTheme.completed,
                      ),
                      const SizedBox(
                        height: 36,
                        child: VerticalDivider(color: AppTheme.border),
                      ),
                      _StatColumn(
                        label: 'Total Visits',
                        value:
                            '${summary.activeTicketsCount + summary.pastVisitsCount}',
                        color: AppTheme.primary,
                      ),
                    ],
                  ),
                ),
              ),
              loading: () => const SizedBox.shrink(),
              error: (_, _) => const SizedBox.shrink(),
            ),
            const SizedBox(height: 16),

            // Profile Information Details
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Account Details',
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 16),
                    _ProfileDetailTile(
                      icon: Icons.person_outline,
                      label: 'Full Name',
                      value: user?.name ?? '--',
                    ),
                    const Divider(height: 20, color: AppTheme.border),
                    _ProfileDetailTile(
                      icon: Icons.email_outlined,
                      label: 'Email',
                      value: user?.email ?? '--',
                    ),
                    const Divider(height: 20, color: AppTheme.border),
                    _ProfileDetailTile(
                      icon: Icons.phone_outlined,
                      label: 'Phone Number',
                      value: (user?.phone != null && user!.phone!.isNotEmpty)
                          ? user.phone!
                          : 'Not provided',
                    ),
                    const Divider(height: 20, color: AppTheme.border),
                    _ProfileDetailTile(
                      icon: Icons.security_outlined,
                      label: 'Authorized Role',
                      value: user?.role.toUpperCase() ?? 'PATIENT',
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Server & Settings Card
            Card(
              child: Column(
                children: [
                  ListTile(
                    leading: const Icon(Icons.dns_outlined, color: AppTheme.primary),
                    title: const Text('Backend API Server'),
                    subtitle: Text(
                      ApiConfig.baseUrl,
                      style: const TextStyle(fontSize: 12),
                      overflow: TextOverflow.ellipsis,
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => ServerSettingsDialog.show(context),
                  ),
                  const Divider(height: 1, color: AppTheme.border),
                  const ListTile(
                    leading: Icon(Icons.info_outline, color: AppTheme.accent),
                    title: Text('Queueless Hospital System'),
                    subtitle: Text('Version 1.0.0 • Mobile Client for Patients'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Logout Button
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.error,
                foregroundColor: Colors.white,
              ),
              icon: const Icon(Icons.logout_rounded),
              label: const Text('Sign Out'),
              onPressed: () => _logout(context, ref),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}

class _StatColumn extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _StatColumn({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w800,
            color: color,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
        ),
      ],
    );
  }
}

class _ProfileDetailTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _ProfileDetailTile({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 20, color: AppTheme.textSecondary),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontSize: 11,
                  color: AppTheme.textSecondary,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
