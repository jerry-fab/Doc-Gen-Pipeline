using System;
using System.Threading.Tasks;

namespace ECommerce.Services
{
    public interface IPaymentGateway
    {
        Task<bool> ChargeAsync(string customerId, decimal amount);
    }

    public class OrderService : IPaymentGateway
    {
        private readonly IPaymentGateway _gateway;
        private readonly string _merchantId;

        public OrderService(IPaymentGateway gateway, string merchantId)
        {
            _gateway = gateway;
            _merchantId = merchantId;
        }

        public async Task<bool> ChargeAsync(string customerId, decimal amount)
        {
            if (amount <= 0) return false;
            return await _gateway.ChargeAsync(customerId, amount);
        }

        public string GetOrderStatus(string orderId)
        {
            return "Shipped";
        }
    }
}
