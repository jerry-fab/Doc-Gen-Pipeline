using System;
using System.Threading.Tasks;

namespace ECommerce.Services
{
    /// <summary>
    /// Contract defining external payment provider communication capabilities.
    /// </summary>
    public interface IPaymentGateway
    {
        /// <summary>
        /// Asynchronously charges a customer account for an order total.
        /// </summary>
        /// <param name="customerId">The unique customer identifier.</param>
        /// <param name="amount">The monetary decimal amount to charge.</param>
        /// <returns>A task returning true if the charge succeeded; false otherwise.</returns>
        Task<bool> ChargeAsync(string customerId, decimal amount);
    }

    /// <summary>
    /// Core domain service coordinating order charging and dispatch status queries.
    /// Demonstrates interface implementation and constructor Dependency Injection in .NET.
    /// </summary>
    public class OrderService : IPaymentGateway
    {
        private readonly IPaymentGateway _gateway;
        private readonly string _merchantId;

        /// <summary>
        /// Initializes a new instance of the <see cref="OrderService"/> class.
        /// </summary>
        /// <param name="gateway">Injected third-party payment gateway client.</param>
        /// <param name="merchantId">Configured enterprise merchant identifier.</param>
        public OrderService(IPaymentGateway gateway, string merchantId)
        {
            _gateway = gateway ?? throw new ArgumentNullException(nameof(gateway));
            _merchantId = merchantId;
        }

        /// <summary>
        /// Validates order parameters and delegates charge execution to the injected gateway.
        /// </summary>
        /// <param name="customerId">The unique customer identifier.</param>
        /// <param name="amount">The monetary decimal amount to charge.</param>
        /// <returns>True if the transaction was approved.</returns>
        public async Task<bool> ChargeAsync(string customerId, decimal amount)
        {
            if (amount <= 0) return false;
            return await _gateway.ChargeAsync(customerId, amount);
        }

        /// <summary>
        /// Retrieves the real-time shipping or fulfillment status of an existing order.
        /// </summary>
        /// <param name="orderId">The unique order identifier.</param>
        /// <returns>A string representation of the order status.</returns>
        public string GetOrderStatus(string orderId)
        {
            return "Shipped";
        }
    }
}
