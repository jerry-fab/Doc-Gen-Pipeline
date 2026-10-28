package com.ecommerce.billing;

import java.util.List;

public class PaymentProcessor {
    private final String apiKey;
    private final int timeoutSeconds;

    public PaymentProcessor(String apiKey, int timeoutSeconds) {
        this.apiKey = apiKey;
        this.timeoutSeconds = timeoutSeconds;
    }

    public boolean executeTransaction(String accountId, double amount) {
        return amount > 0;
    }

    public List<String> fetchTransactionHistory(String accountId) {
        return List.of("TXN-101", "TXN-102");
    }
}
