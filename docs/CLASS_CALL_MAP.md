# Definitions

AuthController     -> src/controllers/auth_controller.py
OrderController     -> src/controllers/order_controller.py
PaymentController   -> src/controllers/payment_controller.py

AuthService          -> src/services/auth_service.py
OrderService          -> src/services/order_service.py
PaymentService        -> src/services/payment_service.py
InventoryService      -> src/services/inventory_service.py

UserRepository       -> src/repositories/user_repository.py
OrderRepository       -> src/repositories/order_repository.py
InventoryRepository   -> src/repositories/inventory_repository.py

JwtHelper            -> src/utils/jwt_helper.py
AuditLogger           -> src/utils/audit_logger.py
Notifier              -> src/utils/notifier.py
PaymentGatewayClient  -> src/utils/payment_gateway.py

# Usage Chain (verified against actual `import` statements, not hand-authored)

AuthController
 -> AuthService
    -> UserRepository
    -> JwtHelper
    -> AuditLogger

OrderController
 -> OrderService
    -> OrderRepository
    -> InventoryService
       -> InventoryRepository
       -> AuditLogger
    -> Notifier
    -> AuditLogger

PaymentController
 -> PaymentService
    -> UserRepository
    -> PaymentGatewayClient
    -> Notifier
    -> AuditLogger

# Fan-in (who uses each shared utility)

AuditLogger    <- AuthService, InventoryService, OrderService, PaymentService
Notifier       <- OrderService, PaymentService
UserRepository <- AuthService, PaymentService
