package com.leesolomon.banktts;

import android.app.Notification;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.util.Log;

public class NotificationService extends NotificationListenerService {

    private static final String TAG = "BankNotification";

    @Override
    public void onListenerConnected() {
        super.onListenerConnected();
        Log.d(TAG, "알림 리스너 연결됨");
    }

    @Override
    public void onListenerDisconnected() {
        super.onListenerDisconnected();
        Log.d(TAG, "알림 리스너 연결 해제됨");
    }

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn == null || sbn.getNotification() == null) {
            return;
        }

        Notification notification = sbn.getNotification();
        Bundle extras = notification.extras;

        if (extras == null) {
            return;
        }

        String packageName = sbn.getPackageName();

        CharSequence titleValue =
                extras.getCharSequence(Notification.EXTRA_TITLE);

        CharSequence textValue =
                extras.getCharSequence(Notification.EXTRA_TEXT);

        String title =
                titleValue == null ? "" : titleValue.toString();

        String text =
                textValue == null ? "" : textValue.toString();

        Log.d(TAG, "패키지: " + packageName);
        Log.d(TAG, "제목: " + title);
        Log.d(TAG, "내용: " + text);

    getSharedPreferences("bank_notifications", MODE_PRIVATE)
        .edit()
        .putString("package_name", packageName)
        .putString("title", title)
        .putString("text", text)
        .putLong("notification_id", System.currentTimeMillis())
        .apply();

    Log.d(TAG, "Python 전달용 알림 저장 완료");
    }

    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {
        super.onNotificationRemoved(sbn);
    }
}