package com.fertilisense.fertilisense;

import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.MenuItem;
import android.view.View;
import android.widget.Button;
import java.io.File;
import java.util.HashMap;
import java.util.Map;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.GravityCompat;
import androidx.drawerlayout.widget.DrawerLayout;
import android.widget.LinearLayout;

import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.google.android.material.navigation.NavigationView;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;
import com.google.firebase.firestore.DocumentSnapshot;
import com.google.firebase.firestore.FirebaseFirestore;
import com.prolificinteractive.materialcalendarview.MaterialCalendarView;
import com.squareup.picasso.Picasso;

import android.net.Uri;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.List;

import android.content.pm.PackageManager;

import android.os.Environment;
import java.io.FileOutputStream;

import android.graphics.pdf.PdfDocument;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Color;

import com.google.firebase.database.ServerValue; // Add this import

public class ReportActivity extends AppCompatActivity implements NavigationView.OnNavigationItemSelectedListener {
    private static final int STORAGE_PERMISSION_CODE = 100;

    private TextView cyclesInfoTextView;
    private TextView symptomsInfoTextView;
    private DrawerLayout drawerLayout;
    private NavigationView navigationView;
    private BottomNavigationView bottomNavigationView;
    private FirebaseAuth authProfile;
    private String appPackageName;
    private PdfDocument pdfDocument;

    private static final String TAG = "ReportActivity";
    private MaterialCalendarView calendarView;
    private FirebaseFirestore db;

    private TextView cyclesInfo, symptomsInfo;
    private Button downloadButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_report);

        // Initialize FirebaseAuth and Firestore
        authProfile = FirebaseAuth.getInstance();
        db = FirebaseFirestore.getInstance();

        // Initialize navigation components
        drawerLayout = findViewById(R.id.drawer_layout);
        navigationView = findViewById(R.id.nav_view);
        bottomNavigationView = findViewById(R.id.bottom_navigation);

        // Initialize the appPackageName inside onCreate
        appPackageName = getPackageName();

        cyclesInfoTextView = findViewById(R.id.cycles_info);
        symptomsInfoTextView = findViewById(R.id.symptoms_info);

        // Initialize TextViews
        cyclesInfo = findViewById(R.id.cycles_info);
        symptomsInfo = findViewById(R.id.symptoms_info);

        // Initialize download button
        LinearLayout downloadLayout = findViewById(R.id.download_report);
        downloadLayout.setOnClickListener(v -> {
            downloadReport();
        });

        // Load user information in the navigation header
        loadUserInformation();

        fetchMenstrualCycleData();
        fetchSymptomData();

        // Set up the drawer and bottom navigation listeners
        findViewById(R.id.ic_menu).setOnClickListener(v -> drawerLayout.openDrawer(GravityCompat.START));

        // Set navigation item selected listener
        navigationView.setNavigationItemSelectedListener(this);

        bottomNavigationView.setOnNavigationItemSelectedListener(item -> {
            int id = item.getItemId();

            if (id == R.id.genital) {
                Intent intent = new Intent(ReportActivity.this, FemaleReproductiveSystemActivity.class);
                startActivity(intent);
                overridePendingTransition(0, 0);
                finish();
            } else if (id == R.id.calendar) {
                Log.d("FertiliSense", "Checking cycle logs before navigating to CalendarActivity");
                checkForLoggedCyclesAndShowDialog();
            } else if (id == R.id.home) {
                Intent intent = new Intent(ReportActivity.this, FertiliSenseDashboardActivity.class);
                startActivity(intent);
                overridePendingTransition(0, 0);
                finish();
            } else if (id == R.id.chatbot) {
                Intent intent = new Intent(ReportActivity.this, ChatBotActivity.class);
                startActivity(intent);
                overridePendingTransition(0, 0);
                finish();
            } else if (id == R.id.report) {
                Log.d("FertiliSense", "User report details clicked");
            }

            return true;
        });

        // Set "Report" as the default selected item in bottom navigation
        bottomNavigationView.setSelectedItemId(R.id.report);
    }

    private void downloadReport() {
        PdfDocument pdfDocument = new PdfDocument();
        PdfDocument.PageInfo pageInfo = new PdfDocument.PageInfo.Builder(595, 842, 1).create();
        PdfDocument.Page page = pdfDocument.startPage(pageInfo);

        Canvas canvas = page.getCanvas();
        Paint paint = new Paint();
        paint.setTextSize(12);
        paint.setColor(Color.BLACK);

        StringBuilder reportContentBuilder = new StringBuilder();
        reportContentBuilder.append("Menstrual Cycle Data:\n")
                .append("Start Date: ").append(cyclesInfo.getText().toString()).append("\n")
                .append("End Date: \n")
                .append("Cycle Duration: \n")
                .append("Period Duration: \n\n")
                .append("Symptom Data:\n")
                .append(symptomsInfo.getText().toString()).append("\n\n");

        String reportContent = reportContentBuilder.toString();
        float yPosition = 25;
        for (String line : reportContent.split("\n")) {
            canvas.drawText(line, 10, yPosition, paint);
            yPosition += 20;
        }

        pdfDocument.finishPage(page);

        // Save the report to the Firebase Realtime Database
        Map<String, Object> reportData = new HashMap<>();
        reportData.put("reportContent", reportContent);
        reportData.put("timestamp", ServerValue.TIMESTAMP); // Use ServerValue to add a timestamp

        String userId = authProfile.getCurrentUser().getUid();
        DatabaseReference reportsRef = FirebaseDatabase.getInstance().getReference("reports").child(userId);

        reportsRef.push().setValue(reportData).addOnCompleteListener(task -> {
            if (task.isSuccessful()) {
                Toast.makeText(this, "Report saved to Firebase Realtime Database", Toast.LENGTH_SHORT).show();

                // Save the PDF file locally in the app's external files directory (Scoped Storage)
                File appDownloadsDir = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
                File pdfFile = new File(appDownloadsDir, "report.pdf");

                try {
                    FileOutputStream fileOutputStream = new FileOutputStream(pdfFile);
                    pdfDocument.writeTo(fileOutputStream);
                    fileOutputStream.close();
                    Toast.makeText(this, "Successfully Downloaded Report: " + pdfFile.getAbsolutePath(), Toast.LENGTH_SHORT).show();
                } catch (Exception e) {
                    e.printStackTrace();
                    Toast.makeText(this, "Failed to download report: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                } finally {
                    pdfDocument.close(); // Ensure the document is closed
                }

            } else {
                Toast.makeText(this, "Failed to save report: " + task.getException().getMessage(), Toast.LENGTH_SHORT).show();
                pdfDocument.close(); // Ensure document is closed if the Firebase save fails
            }
        });
    }


    // This method should handle the result of the permission request
    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == STORAGE_PERMISSION_CODE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                // Permission granted, proceed to save PDF
                savePdf(pdfDocument);
            } else {
                Toast.makeText(this, "Permission denied to write to external storage", Toast.LENGTH_SHORT).show();
            }
        }
    }

    private void savePdf(PdfDocument pdfDocument) {
        // Use the app's private storage or scoped storage
        File reportFile = new File(getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "report.pdf");

        // Create the directory if it doesn't exist
        if (!reportFile.getParentFile().exists()) {
            reportFile.getParentFile().mkdirs();
        }

        try {
            // Write the PDF document to the file
            pdfDocument.writeTo(new FileOutputStream(reportFile));
            Toast.makeText(this, "Successfully Downloaded Report: " + reportFile.getAbsolutePath(), Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            e.printStackTrace();
            Toast.makeText(this, "Failed to download report: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        } finally {
            pdfDocument.close();
        }
    }

    private void fetchMenstrualCycleData() {
        FirebaseUser currentUser = authProfile.getCurrentUser();
        if (currentUser != null) {
            String userId = currentUser.getUid();
            Log.d(TAG, "Fetching menstrual cycle data for user ID: " + userId);

            db.collection("menstrual_cycles")
                    .document(userId)
                    .get()
                    .addOnCompleteListener(task -> {
                        if (task.isSuccessful()) {
                            DocumentSnapshot document = task.getResult();
                            if (document != null && document.exists()) {
                                // Log the entire document
                                Log.d(TAG, "Document data: " + document.getData());

                                // Get the cycles list from Firestore
                                List<Map<String, Object>> cycles = (List<Map<String, Object>>) document.get("cycles");
                                if (cycles != null && !cycles.isEmpty()) {
                                    StringBuilder cyclesInfo = new StringBuilder(); // To hold all cycle info

                                    // Iterate through each cycle and log the information
                                    for (Map<String, Object> cycle : cycles) {
                                        // Safely retrieve each field, handling both Long and String types
                                        String cycleDuration = getStringFromObject(cycle.get("cycle_duration"));
                                        String endDate = getStringFromObject(cycle.get("end_date"));
                                        String periodDuration = getStringFromObject(cycle.get("period_duration"));
                                        String startDate = getStringFromObject(cycle.get("start_date"));

                                        // Log each cycle's information
//                                        Log.d(TAG, "Cycle Duration: " + cycleDuration);
//                                        Log.d(TAG, "End Date: " + endDate);
//                                        Log.d(TAG, "Period Duration: " + periodDuration);
//                                        Log.d(TAG, "Start Date: " + startDate);

                                        // Append the information to cyclesInfo in the desired order
                                        cyclesInfo.append("Start Date: ").append(startDate != null ? startDate : "N/A").append("\n")
                                                .append("End Date: ").append(endDate != null ? endDate : "N/A").append("\n")
                                                .append("Cycle Duration: ").append(cycleDuration != null ? cycleDuration : "N/A").append("\n")
                                                .append("Period Duration: ").append(periodDuration != null ? periodDuration : "N/A").append("\n\n");
                                    }

                                    // Update the UI on the main thread
                                    runOnUiThread(() -> {
                                        TextView cyclesTextView = findViewById(R.id.cycles_info); // Assuming you have a TextView to display all cycle info
                                        cyclesTextView.setText(cyclesInfo.toString());
                                    });
                                } else {
                                    Log.d(TAG, "No cycles found for user ID: " + userId);
                                }
                            } else {
                                Log.d(TAG, "No menstrual cycle data found for user ID: " + userId);
                            }
                        } else {
                            Log.e(TAG, "Error fetching menstrual cycle data: " + task.getException());
                        }
                    });
        } else {
            Log.d(TAG, "No user is signed in");
        }
    }

    // Helper method to safely convert Object to String
    private String getStringFromObject(Object obj) {
        if (obj instanceof Long) {
            return String.valueOf((Long) obj); // Convert Long to String
        } else if (obj instanceof String) {
            return (String) obj; // Cast directly if it's a String
        } else {
            return null; // Return null or handle the unexpected case
        }
    }

    private void fetchSymptomData() {
        FirebaseUser currentUser = authProfile.getCurrentUser();
        if (currentUser != null) {
            String userId = currentUser.getUid();
            Log.d(TAG, "Fetching symptom data for user ID: " + userId);

            db.collection("symptom_logs")
                    .document(userId)
                    .get()
                    .addOnCompleteListener(task -> {
                        if (task.isSuccessful()) {
                            DocumentSnapshot document = task.getResult();
                            if (document != null && document.exists()) {
                                // Log the entire document
                                Log.d(TAG, "Document data: " + document.getData());

                                // Get the logs list from Firestore
                                List<Map<String, Object>> logs = (List<Map<String, Object>>) document.get("logs");
                                if (logs != null && !logs.isEmpty()) {
                                    StringBuilder symptomsInfo = new StringBuilder(); // To hold all symptom info

                                    // Log the entire logs structure for debugging
                                    Log.d(TAG, "Logs: " + logs.toString());

                                    // Iterate through each log and log the information
                                    for (Map<String, Object> log : logs) {
                                        String symptom = (String) log.get("symptoms");
                                        // Use the correct keys to access start_dates and end_dates
                                        String startDate = (String) log.get("start_dates");
                                        String endDate = (String) log.get("end_dates");

                                        // Log each symptom's information
                                        Log.d(TAG, "Symptom: " + symptom);
                                        Log.d(TAG, "Symptom Start: " + startDate);
                                        Log.d(TAG, "Symptom End: " + endDate);

                                        // Append the information to symptomsInfo
                                        symptomsInfo.append("Start Date: ").append(startDate != null ? startDate : "N/A").append("\n")
                                                .append("End Date: ").append(endDate != null ? endDate : "N/A").append("\n")
                                                .append("Symptom: ").append(symptom != null ? symptom : "N/A").append("\n\n");
                                    }

                                    // Update the UI on the main thread
                                    runOnUiThread(() -> {
                                        TextView symptomsTextView = findViewById(R.id.symptoms_info); // Assuming you have a TextView to display symptoms
                                        symptomsTextView.setText(symptomsInfo.toString());
                                    });
                                } else {
                                    Log.d(TAG, "No logs found for user ID: " + userId);
                                }
                            } else {
                                Log.d(TAG, "No symptom data found for user ID: " + userId);
                            }
                        } else {
                            Log.e(TAG, "Error fetching symptom data: " + task.getException());
                        }
                    });
        } else {
            Log.d(TAG, "No user is signed in");
        }
    }

    private void loadUserInformation() {
        View headerView = navigationView.getHeaderView(0);
        TextView usernameTextView = headerView.findViewById(R.id.nav_drawer_username);
        TextView emailTextView = headerView.findViewById(R.id.nav_drawer_email);
        ImageView profilePictureView = findViewById(R.id.nav_header_profile_picture); // Add this

        FirebaseUser user = authProfile.getCurrentUser();
        if (user != null) {
            String email = user.getEmail();
            emailTextView.setText(email);

            // Fetch username from the database
            DatabaseReference referenceProfile = FirebaseDatabase.getInstance().getReference("Registered Users");
            String userId = user.getUid();
            Log.d("FertiliSense", "Fetching data for user ID: " + userId);

            referenceProfile.child(userId).addListenerForSingleValueEvent(new ValueEventListener() {
                @Override
                public void onDataChange(@NonNull DataSnapshot snapshot) {
                    if (snapshot.exists()) {
                        String username = snapshot.child("username").getValue(String.class);
                        if (username != null && !username.isEmpty()) {
                            usernameTextView.setText(username);
                        }

                        // Fetch the profile picture from FirebaseUser
                        Uri photoUri = user.getPhotoUrl();
                        if (photoUri != null) {
                            Picasso.with(ReportActivity.this)
                                    .load(photoUri)
                                    .placeholder(R.drawable.ic_user) // Fallback image
                                    .transform(new CircleTransform()) // Make the image circular
                                    .into(profilePictureView);
                        } else {
                            Log.d("FertiliSense", "User does not have a profile picture");
                        }
                    } else {
                        Toast.makeText(ReportActivity.this, "User data not found", Toast.LENGTH_SHORT).show();
                    }
                }

                @Override
                public void onCancelled(@NonNull DatabaseError error) {
                    Toast.makeText(ReportActivity.this, "Something went wrong", Toast.LENGTH_SHORT).show();
                }
            });

            // Set a click listener to open UserProfileActivity
            headerView.setOnClickListener(v -> {
                Intent intent = new Intent(ReportActivity.this, UserProfileActivity.class);
                startActivity(intent);
            });
        } else {
            Log.d("FertiliSense", "No current user logged in");
        }
    }

    private void checkForLoggedCyclesAndShowDialog() {
        FirebaseUser currentUser = authProfile.getCurrentUser();
        if (currentUser != null) {
            String userId = currentUser.getUid();

            db.collection("menstrual_cycles")
                    .document(userId)
                    .get()
                    .addOnSuccessListener(documentSnapshot -> {
                        if (!documentSnapshot.exists()) {
                            showCycleLogDialog();
                        } else {
                            navigateToCalendarActivity();
                        }
                    })
                    .addOnFailureListener(e -> {
                        Toast.makeText(ReportActivity.this, "Error checking cycle data", Toast.LENGTH_SHORT).show();
                    });
        } else {
            Toast.makeText(this, "No user logged in", Toast.LENGTH_SHORT).show();
        }
    }

    private void showCycleLogDialog() {
        new AlertDialog.Builder(this)
                .setTitle("Log Menstrual Cycle")
                .setMessage("You haven't logged any menstrual cycle yet. Would you like to log it now?")
                .setPositiveButton("OK", (dialog, which) -> navigateToChatBotActivity())
                .setNegativeButton("Cancel", (dialog, which) -> navigateToCalendarActivity())
                .setCancelable(false)
                .show();
    }

    private void navigateToCalendarActivity() {
        Intent intent = new Intent(ReportActivity.this, CalendarActivity.class);
        startActivity(intent);
        overridePendingTransition(0, 0);
        finish();
    }

    private void navigateToChatBotActivity() {
        Intent intent = new Intent(ReportActivity.this, ChatBotActivity.class);
        startActivity(intent);
        overridePendingTransition(0, 0);
        finish();
    }

    @Override
    public boolean onNavigationItemSelected(@NonNull MenuItem item) {
        int id = item.getItemId();

        if (id == R.id.share_us) {
            Intent intent = new Intent(Intent.ACTION_SEND);
            intent.setType("text/plain");
            intent.putExtra(Intent.EXTRA_TEXT, "Download this app: https://play.google.com/store/apps/details?id=" + appPackageName);
            startActivity(Intent.createChooser(intent, "Share this app"));
        } else if (id == R.id.rate_us) {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse("https://play.google.com/store/apps/details?id=" + appPackageName));
            startActivity(intent);
            overridePendingTransition(0, 0);
            finish();
        } else if (id == R.id.feedback) {
            Intent intent = new Intent(ReportActivity.this, FeedbackActivity.class);
            startActivity(intent);
            overridePendingTransition(0, 0);
            finish();
        } else if (id == R.id.privacy) {
            Intent intent = new Intent(ReportActivity.this, PrivacyPolicyActivity.class);
            startActivity(intent);
            overridePendingTransition(0, 0);
            finish();
        } else if (id == R.id.disclaimer_content) {
            Intent intent = new Intent(ReportActivity.this, DisclaimerContentActivity.class);
            startActivity(intent);
            overridePendingTransition(0, 0);
            finish();
        } else if (id == R.id.terms_condition) {
            Intent intent = new Intent(ReportActivity.this, TermsAndConditionContentActivity.class);
            startActivity(intent);
            overridePendingTransition(0, 0);
            finish();
        } else if (id == R.id.user_manual) {
            Log.d("FertiliSense", "User Manual clicked");
            Intent intent = new Intent(ReportActivity.this, UserManualActivity.class);
            startActivity(intent);
            overridePendingTransition(0, 0);
            finish();
        } else if (id == R.id.logout) {
            authProfile.signOut();
            Intent intent = new Intent(ReportActivity.this, LoginActivity.class);
            startActivity(intent);
            finish();
        }
        drawerLayout.closeDrawer(GravityCompat.START);
        return true;
    }
}