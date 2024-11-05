package com.fertilisense.fertilisense;

import androidx.annotation.NonNull;
import androidx.appcompat.app.ActionBar;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.TextView;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MaleChatBotActivity extends AppCompatActivity {
    RecyclerView recyclerView;
    TextView welcomeTextView;
    EditText messageEditText;
    ImageButton sendButton;
    List<Message> messageList;
    MessageAdapter messageAdapter;
    public static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    OkHttpClient client = new OkHttpClient();

    // Firebase references
    private FirebaseAuth auth;
    private DatabaseReference chatReference;

    private FirebaseUser currentUser;

    private final String chatUrl = "https://cdd4-2001-4452-480-9600-8467-842-3811-aad1.ngrok-free.app/webhooks/rest/webhook";
    //private final String actionUrl = "https://2c12-2001-4452-409-cc00-784a-f1c-c946-7897.ngrok-free.app/webhook";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_chat_bot);

        // Set up the toolbar
        ActionBar actionBar = getSupportActionBar();
        if (actionBar != null) {
            actionBar.setTitle("FertiliSense ChatBot");
            actionBar.setDisplayHomeAsUpEnabled(true);
            actionBar.setHomeAsUpIndicator(R.drawable.ic_back_button_white);
        }

        // Initialize Firebase Auth and Database
        auth = FirebaseAuth.getInstance();
        chatReference = FirebaseDatabase.getInstance().getReference("Chat");
        currentUser = auth.getCurrentUser();

        messageList = new ArrayList<>();

        recyclerView = findViewById(R.id.recyclerView);
        messageEditText = findViewById(R.id.message_edit_text);
        sendButton = findViewById(R.id.send_btn);

        // Setup recycler view
        messageAdapter = new MessageAdapter(messageList);
        recyclerView.setAdapter(messageAdapter);
        LinearLayoutManager llm = new LinearLayoutManager(this);
        llm.setStackFromEnd(true);
        recyclerView.setLayoutManager(llm);

        // Show the welcome message as soon as the chatbot starts
        String welcomeMessage = "Welcome to FertiliSense! How can I assist you today?";
        addToChat(welcomeMessage, Message.SENT_BY_BOT);

        // Send message button logic
        sendButton.setOnClickListener((v) -> {
            String question = messageEditText.getText().toString().trim();
            if (!question.isEmpty()) {
                runOnUiThread(() -> {
                    addToChat(question, Message.SENT_BY_ME);
                    messageEditText.setText("");
                    callAPI(question);
                });
            }
        });
    }

    @Override
    public void onBackPressed() {
        Intent intent = new Intent(MaleChatBotActivity.this, MaleDashboardActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(intent);
        overridePendingTransition(0,0);
        finish();
    }

    void addToChat(String message, String sentBy) {
        runOnUiThread(() -> {
            // Save the message to Firebase Realtime Database
            if (currentUser != null) {
                String senderId = currentUser.getUid();
                String senderName = currentUser.getDisplayName() != null ? currentUser.getDisplayName() : "Anonymous";

                // Save message in Firebase
                DatabaseReference newMessageRef = chatReference.push();
                newMessageRef.setValue(new Message(message, sentBy, senderId, senderName));

                messageList.add(new Message(message, sentBy, senderId, senderName, currentUser.getPhotoUrl()));
            }else {
                messageList.add(new Message(message, sentBy));
            }
            messageAdapter.notifyDataSetChanged();
            recyclerView.smoothScrollToPosition(messageAdapter.getItemCount());
        });
    }

    void addResponse(String response) {
        int index = messageList.size() - 1;
        if (index >= 0 && Message.SENT_BY_BOT.equals(messageList.get(index).getSentBy()) && "Typing...".equals(messageList.get(index).getMessage())) {
            messageList.remove(index);
        }
        addToChat(response, Message.SENT_BY_BOT);
    }

    void callAPI(String question) {
        messageList.add(new Message("Typing...", Message.SENT_BY_BOT));
        recyclerView.smoothScrollToPosition(messageAdapter.getItemCount());

        JSONObject jsonBody = new JSONObject();
        try {
            if (currentUser != null) {
                String senderId = currentUser.getUid();
                String senderName = currentUser.getDisplayName() != null ? currentUser.getDisplayName() : "Anonymous";

                jsonBody.put("sender", senderId);
                jsonBody.put("sender_name", senderName);
                jsonBody.put("message", question);
            } else {
                jsonBody.put("sender", "unknown");
                jsonBody.put("message", question);
            }
        } catch (JSONException e) {
            e.printStackTrace();
            addResponse("Failed to create JSON payload: " + e.getMessage());
            return;
        }

        RequestBody body = RequestBody.create(jsonBody.toString(), JSON);

        Request request = new Request.Builder()
                //.url(question.charAt(0) == '/'? actionUrl : chatUrl)
                .url(chatUrl)
                .header("Content-Type", "application/json")
                .post(body)
                .build();

        Log.d("ChatBotActivity", "Request URL: " + request.url());
        Log.d("ChatBotActivity", "Request Body: " + body.toString());

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) {
                addResponse("Failed to load check your internet connectivity.");
            }

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) throws IOException {
                if (response.isSuccessful()) {
                    try {
                        String responseBody = response.body() != null ? response.body().string() : "No response body";
                        Log.d("ChatBotActivity", "Response: " + responseBody);

                        // If response body is null or empty
                        if (responseBody == null || responseBody.isEmpty()) {
                            addResponse("No valid data received from the server.");
                            return;
                        }

                        Gson gson = new Gson();
                        Type dataType = new TypeToken<List<ResponseModel>>() {}.getType();
                        List<ResponseModel> data = gson.fromJson(responseBody, dataType);

                        if (data != null && !data.isEmpty()) {
                            for (ResponseModel item : data) {
                                if (item.getText() != null) {
                                    addResponse(item.getText());
                                } else if (item.getImage() != null) {
                                    addResponse(item.getImage());
                                } else {
                                    addResponse("Received an empty response.");
                                }
                            }
                        } else {
                            Log.d("ChatBotActivity", "Response data is empty or null");
                            addResponse("No valid data received from the server.");
                        }
                    } catch (Exception e) {
                        Log.e("ChatBotActivity", "Error processing response: " + e.getMessage());
                        addResponse("Failed to process response due to " + e.getMessage());
                    }
                } else {
                    Log.e("ChatBotActivity", "Failed to load response: " + response.message());
                    addResponse("Failed to load response due to " + response.message());
                }
            }

        });

    }
}