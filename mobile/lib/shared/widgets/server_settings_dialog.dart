import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../core/config/api_config.dart';
import '../../core/theme/app_theme.dart';

/// Interactive dialog allowing configuration of the backend API base URL
/// (e.g. for switching between Android emulator 10.0.2.2 and physical phone LAN IP).
class ServerSettingsDialog extends StatefulWidget {
  const ServerSettingsDialog({super.key});

  static Future<void> show(BuildContext context) {
    return showDialog(
      context: context,
      builder: (ctx) => const ServerSettingsDialog(),
    );
  }

  @override
  State<ServerSettingsDialog> createState() => _ServerSettingsDialogState();
}

class _ServerSettingsDialogState extends State<ServerSettingsDialog> {
  late final TextEditingController _urlController;
  bool _isTesting = false;
  String? _testResult;
  bool _testSuccess = false;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: ApiConfig.baseUrl);
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _testConnection() async {
    setState(() {
      _isTesting = true;
      _testResult = null;
    });

    final testUrl = _urlController.text.trim();
    final healthUrl = testUrl.endsWith('/')
        ? '${testUrl}health'
        : '$testUrl/health';

    try {
      final dio = Dio(
        BaseOptions(
          connectTimeout: const Duration(seconds: 4),
          receiveTimeout: const Duration(seconds: 4),
        ),
      );
      final res = await dio.get(healthUrl);
      if (res.statusCode == 200) {
        setState(() {
          _testSuccess = true;
          _testResult = 'Connection successful! Server is healthy.';
        });
      } else {
        setState(() {
          _testSuccess = false;
          _testResult = 'Server responded with status ${res.statusCode}.';
        });
      }
    } catch (e) {
      setState(() {
        _testSuccess = false;
        _testResult = 'Connection failed: Unable to reach $testUrl';
      });
    } finally {
      setState(() {
        _isTesting = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Row(
        children: [
          Icon(Icons.dns_rounded, color: AppTheme.primary),
          SizedBox(width: 10),
          Expanded(
            child: Text('Backend Server API'),
          ),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Configure the Flask backend API base URL:',
              style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 6),
            const Text(
              '• Android Emulator: http://10.0.2.2:5000/api/v1\n'
              '• Physical Device: http://<computer-lan-ip>:5000/api/v1',
              style: TextStyle(fontSize: 11, color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _urlController,
              decoration: const InputDecoration(
                labelText: 'Base URL',
                hintText: 'http://10.0.2.2:5000/api/v1',
              ),
            ),
            const SizedBox(height: 12),
            if (_isTesting)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(8.0),
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            if (_testResult != null)
              Container(
                margin: const EdgeInsets.only(top: 8),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: _testSuccess
                      ? AppTheme.completed.withAlpha(25)
                      : AppTheme.error.withAlpha(25),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: _testSuccess ? AppTheme.completed : AppTheme.error,
                  ),
                ),
                child: Text(
                  _testResult!,
                  style: TextStyle(
                    fontSize: 12,
                    color: _testSuccess ? AppTheme.completed : AppTheme.error,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _testConnection,
          child: const Text('Test Connection'),
        ),
        TextButton(
          onPressed: () {
            ApiConfig.resetToDefault();
            _urlController.text = ApiConfig.baseUrl;
            setState(() {
              _testResult = 'Reset to default: ${ApiConfig.baseUrl}';
              _testSuccess = true;
            });
          },
          child: const Text('Reset'),
        ),
        ElevatedButton(
          onPressed: () {
            ApiConfig.setBaseUrl(_urlController.text.trim());
            Navigator.pop(context);
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('API URL set to: ${ApiConfig.baseUrl}'),
                behavior: SnackBarBehavior.floating,
              ),
            );
          },
          child: const Text('Save'),
        ),
      ],
    );
  }
}
