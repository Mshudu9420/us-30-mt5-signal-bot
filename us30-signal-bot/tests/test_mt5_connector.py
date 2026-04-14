import mt5_mock
import mt5_connector


def test_connect_success_prints_account_info(monkeypatch, capsys):
	monkeypatch.setattr(mt5_connector, "mt5", mt5_mock)
	mt5_mock.shutdown()

	connected = mt5_connector.connect()

	output = capsys.readouterr().out
	assert connected is True
	assert "MT5 connected" in output
	assert "login=" in output
	assert "server=" in output
	assert "balance=" in output


def test_connect_returns_false_when_initialize_fails(monkeypatch, capsys):
	class FailingMT5:
		@staticmethod
		def initialize():
			return False

		@staticmethod
		def last_error():
			return (100, "Init failed")

	monkeypatch.setattr(mt5_connector, "mt5", FailingMT5)

	connected = mt5_connector.connect()

	output = capsys.readouterr().out
	assert connected is False
	assert "MT5 initialization failed" in output
