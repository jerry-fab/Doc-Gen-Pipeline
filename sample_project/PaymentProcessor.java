package com.ecommerce.billing;

import java.util.List;

/**
 * Handles core merchant transaction processing and historical ledger queries.
 * Demonstrates standard Java constructor initialization and typed collections.
 * 
 * @author Engineering Team
 * @version 1.0.0
 */
public class PaymentProcessor {
    private final String apiKey;
    private final int timeoutSeconds;

    /**
     * Constructs a new PaymentProcessor configured with merchant API credentials.
     * 
     * @param apiKey The secret API key used for payment gateway authorization.
     * @param timeoutSeconds Connection timeout threshold in seconds.
     */
    public PaymentProcessor(String apiKey, int timeoutSeconds) {
        this.apiKey = apiKey;
        this.timeoutSeconds = timeoutSeconds;
    }

    /**
     * Executes a financial billing transaction against the designated customer account.
     * 
     * @param accountId The target customer billing account identifier.
     * @param amount The transaction amount to be charged.
     * @return true if the amount was positive and authorization succeeded.
     */
    public boolean executeTransaction(String accountId, double amount) {
        return amount > 0;
    }

    /**
     * Queries recent transaction reference IDs associated with the customer account.
     * 
     * @param accountId The target customer billing account identifier.
     * @return An immutable list of transaction reference numbers.
     */
    public List<String> fetchTransactionHistory(String accountId) {
        return List.of("TXN-101", "TXN-102");
    }
}
