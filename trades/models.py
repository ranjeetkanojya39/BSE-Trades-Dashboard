from django.db import models


class Trade(models.Model):
    trade_id = models.CharField(max_length=32, unique=True)   # unique => duplicates nahi aayenge
    client = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    quantity = models.IntegerField()
    price = models.FloatField()
    timestamp = models.DateTimeField()

    class Meta:
        ordering = ["-id"]

    def to_dict(self):
        return {"id": self.id, "trade_id": self.trade_id, "client": self.client,
                "symbol": self.symbol, "quantity": self.quantity, "price": self.price,
                "timestamp": self.timestamp.isoformat()}
