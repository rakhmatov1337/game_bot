from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
from .models import Player, Team, SoloPlayer, SubscriptionChannel


@method_decorator(csrf_exempt, name='dispatch')
class BotDataView(View):
    """Bot ma'lumotlarini Django bazasiga saqlash uchun API"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Agar alohida jamoa yaratish bo'lsa, boshqa maydonlar kerak emas
            if data.get('action') == 'create_team':
                if 'user_id' not in data or 'team_name' not in data:
                    return JsonResponse({'error': 'user_id va team_name maydonlari kerak'}, status=400)
            else:
                # Ma'lumotlarni tekshirish
                required_fields = ['fullname', 'birthdate', 'freefire_id', 'direction', 'phone', 'user_id', 'registration_type']
                for field in required_fields:
                    if field not in data:
                        return JsonResponse({'error': f'{field} maydoni kerak'}, status=400)
            
            # Agar alohida jamoa yaratish bo'lsa, foydalanuvchini topish
            if data.get('action') == 'create_team':
                try:
                    player = Player.objects.get(user_id=data['user_id'])
                    created = False  # Mavjud foydalanuvchi
                except Player.DoesNotExist:
                    return JsonResponse({'error': 'Foydalanuvchi topilmadi. Avval ro\'yxatdan o\'ting!'}, status=404)
            else:
                # Foydalanuvchini yaratish yoki yangilash
                player, created = Player.objects.get_or_create(
                    user_id=data['user_id'],
                    defaults={
                        'fullname': data['fullname'],
                        'birthdate': data['birthdate'],
                        'freefire_id': data['freefire_id'],
                        'direction': data['direction'],
                        'phone': data['phone'],
                        'username': data.get('username', ''),
                        'registration_type': data['registration_type'],
                    }
                )
            
            # Agar jamoa yaratish bo'lsa (ro'yxatdan o'tish jarayonida)
            if data.get('registration_type') == 'team' and data.get('team_name'):
                if created:
                    team = Team.objects.create(
                        name=data['team_name'],
                        captain=player
                    )
                    player.team = team
                    player.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Jamoa va o\'yinchi yaratildi',
                        'created': True,
                        'team_id': team.id,
                        'referral_code': str(team.referral_code)
                    })
            
            # Agar alohida jamoa yaratish bo'lsa
            if data.get('action') == 'create_team' and data.get('team_name'):
                # Foydalanuvchi allaqachon jamoada ekanligini tekshirish
                if player.team:
                    return JsonResponse({'error': 'Siz allaqachon jamoadasiz!'}, status=400)
                
                team = Team.objects.create(
                    name=data['team_name'],
                    captain=player,
                    direction=player.direction  # Sardorning viloyatini jamoa viloyati sifatida saqlash
                )
                player.team = team
                player.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Jamoa yaratildi',
                    'team_id': team.id,
                    'referral_code': str(team.referral_code)
                })
            
            # Agar jamoa kodiga qo'shilish bo'lsa
            elif data.get('team_id'):
                if created:
                    try:
                        team = Team.objects.get(id=data['team_id'])
                        if not team.is_full:
                            player.team = team
                            player.save()
                            
                            return JsonResponse({
                                'success': True,
                                'message': 'O\'yinchi jamoa kodiga qo\'shildi',
                                'created': True
                            })
                        else:
                            return JsonResponse({'error': 'Jamoa to\'liq'}, status=400)
                    except Team.DoesNotExist:
                        return JsonResponse({'error': 'Jamoa topilmadi'}, status=400)
            
            # Agar solo bo'lsa
            elif data['registration_type'] == 'solo':
                if created:
                    SoloPlayer.objects.create(player=player, looking_for_team=True)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Solo o\'yinchi yaratildi',
                    'created': created
                })
            
            # Agar team bo'lsa (referal kod orqali)
            elif data['registration_type'] == 'team' and not data.get('team_name'):
                # Bu referal kod orqali kelgan foydalanuvchi
                if created:
                    # SoloPlayer yaratmaymiz, chunki u jamoaga qo'shiladi
                    pass
                
                return JsonResponse({
                    'success': True,
                    'message': 'Team player yaratildi',
                    'created': created
                })
            
            return JsonResponse({
                'success': True,
                'message': 'Ma\'lumotlar saqlandi',
                'created': created
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Noto\'g\'ri JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CheckUserView(View):
    """Foydalanuvchi ro'yxatdan o'tganligini tekshirish"""
    
    def get(self, request, user_id):
        try:
            player = Player.objects.get(user_id=user_id)
            return JsonResponse({
                'success': True,
                'registered': True,
                'user_data': {
                    'fullname': player.fullname,
                    'direction': player.direction,
                    'registration_type': player.registration_type,
                    'status': player.status,
                    'created_at': player.created_at.strftime('%d.%m.%Y %H:%M')
                }
            })
        except Player.DoesNotExist:
            return JsonResponse({
                'success': True,
                'registered': False
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TeamsListView(View):
    """Mavjud jamoalar ro'yxatini olish"""
    
    def get(self, request):
        teams = Team.objects.filter(is_active=True)
        # Faqat to'liq bo'lmagan jamoalarni qaytarish
        teams = [team for team in teams if not team.is_full]
        teams_data = []
        
        for team in teams:
            teams_data.append({
                'id': team.id,
                'name': team.name,
                'captain_name': team.captain.fullname,
                'captain_username': team.captain.username or 'username yo\'q',
                'current_members': team.current_members_count,
                'max_members': team.max_members,
                'direction': team.direction,  # Jamoa viloyatini olish
                'available_slots': team.available_slots
            })
        
        return JsonResponse({
            'success': True,
            'teams': teams_data
        })


@method_decorator(csrf_exempt, name='dispatch')
class SoloPlayersListView(View):
    """Solo o'yinchilar ro'yxatini olish"""
    
    def get(self, request):
        # Status bo'yicha solo o'yinchilarni olish
        solo_players = Player.objects.filter(status='solo')
        players_data = []
        
        for player in solo_players:
            players_data.append({
                'id': player.id,
                'fullname': player.fullname,
                'username': player.username or 'username yo\'q',
                'freefire_id': player.freefire_id,
                'direction': player.direction,
                'status': player.get_status_display(),
                'created_at': player.created_at.strftime('%d.%m.%Y')
            })
        
        return JsonResponse({
            'success': True,
            'players': players_data
        })


@method_decorator(csrf_exempt, name='dispatch')
class MyTeamView(View):
    """Foydalanuvchining jamoasini olish"""
    
    def get(self, request, user_id):
        try:
            player = Player.objects.get(user_id=user_id)
            
            if not player.team:
                return JsonResponse({
                    'success': False,
                    'error': 'Foydalanuvchi hech qanday jamoaga qo\'shilmagan'
                }, status=404)
            
            team = player.team
            members_data = []
            
            for member in team.members.all():
                members_data.append({
                    'id': member.id,
                    'fullname': member.fullname,
                    'username': member.username or 'username yo\'q',
                    'is_captain': member == team.captain
                })
            
            return JsonResponse({
                'success': True,
                'team': {
                    'id': team.id,
                    'name': team.name,
                    'captain_name': team.captain.fullname,
                    'current_members': team.current_members_count,
                    'max_members': team.max_members,
                    'referral_code': str(team.referral_code),
                    'is_captain': player == team.captain,
                    'members': members_data
                }
            })
            
        except Player.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Foydalanuvchi topilmadi'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class JoinTeamView(View):
    """Jamoa kodiga qo'shilish"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            team_code = data.get('team_code')
            
            if not user_id or not team_code:
                return JsonResponse({'error': 'user_id va team_code kerak'}, status=400)
            
            # Foydalanuvchini topish
            try:
                player = Player.objects.get(user_id=user_id)
            except Player.DoesNotExist:
                return JsonResponse({'error': 'Foydalanuvchi topilmadi'}, status=404)
            
            # Jamoa kodini topish
            try:
                team = Team.objects.get(referral_code=team_code, is_active=True)
            except Team.DoesNotExist:
                return JsonResponse({'error': 'Noto\'g\'ri jamoa kodi'}, status=400)
            
            # Jamoa to'liq emasligini tekshirish
            if team.is_full:
                return JsonResponse({'error': 'Jamoa to\'liq'}, status=400)
            
            # Foydalanuvchi allaqachon jamoada emasligini tekshirish
            if player.team and player.team.id != team.id:
                return JsonResponse({'error': 'Siz allaqachon boshqa jamoadasiz'}, status=400)
            
            # Viloyat tekshirish - faqat bir xil viloyatdagi o'yinchilar jamoa bo'lishi mumkin
            if player.direction != team.direction:
                return JsonResponse({
                    'error': f'Faqat {team.direction} viloyatidagi o\'yinchilar bu jamoaga qo\'shilishi mumkin. Siz {player.direction} viloyatidasiz.'
                }, status=400)
            
            # Jamoa kodiga qo'shilish
            player.team = team
            player.registration_type = 'team'
            player.save()
            
            # SoloPlayer ni o'chirish (agar mavjud bo'lsa)
            try:
                solo_player = SoloPlayer.objects.get(player=player)
                solo_player.delete()
            except SoloPlayer.DoesNotExist:
                pass  # SoloPlayer mavjud emas, hech narsa qilmaymiz
            
            return JsonResponse({
                'success': True,
                'message': 'Jamoa kodiga muvaffaqiyatli qo\'shildingiz',
                'team_id': team.id,
                'team_name': team.name,
                'captain_name': team.captain.fullname
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Noto\'g\'ri JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionChannelsView(View):
    """Obuna kanallarini olish uchun API"""
    
    def get(self, request):
        channels = SubscriptionChannel.objects.filter(is_active=True)
        channels_data = []
        
        for channel in channels:
            channels_data.append({
                'name': channel.name,
                'type': channel.channel_type,
                'url': channel.url,
                'required': channel.is_required
            })
        
        return JsonResponse({
            'success': True,
            'channels': channels_data
        })


@method_decorator(csrf_exempt, name='dispatch')
class RemoveMemberView(View):
    """Jamoa a'zosini chiqarish"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            captain_id = data.get('captain_id')
            member_id = data.get('member_id')
            
            if not captain_id or not member_id:
                return JsonResponse({'error': 'captain_id va member_id kerak'}, status=400)
            
            # Sardorni topish
            try:
                captain = Player.objects.get(user_id=captain_id)
            except Player.DoesNotExist:
                return JsonResponse({'error': 'Sardor topilmadi'}, status=404)
            
            # Sardor jamoada ekanligini tekshirish
            if not captain.team or captain != captain.team.captain:
                return JsonResponse({'error': 'Siz jamoa sardori emassiz'}, status=403)
            
            # Chiqariladigan a'zoni topish
            try:
                member = Player.objects.get(id=member_id, team=captain.team)
            except Player.DoesNotExist:
                return JsonResponse({'error': 'A\'zo topilmadi'}, status=404)
            
            # Sardorni o'zi chiqarib yuborishga ruxsat bermaslik
            if member == captain:
                return JsonResponse({'error': 'O\'zingizni chiqarib yubora olmaysiz'}, status=400)
            
            # A'zoni jamoadan chiqarish
            member.team = None
            member.registration_type = 'solo'
            member.save()
            
            # Solo o'yinchi sifatida qayta yaratish
            SoloPlayer.objects.get_or_create(player=member, defaults={'looking_for_team': True})
            
            return JsonResponse({
                'success': True,
                'message': f'{member.fullname} jamoadan chiqarildi',
                'member_name': member.fullname
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Noto\'g\'ri JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeleteTeamView(View):
    """Jamoa sardori tomonidan jamoani o'chirish"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            captain_id = data.get('captain_id')
            
            if not captain_id:
                return JsonResponse({'error': 'captain_id kerak'}, status=400)
            
            # Sardorni topish
            try:
                captain = Player.objects.get(user_id=captain_id)
            except Player.DoesNotExist:
                return JsonResponse({'error': 'Sardor topilmadi'}, status=404)
            
            # Sardor jamoada ekanligini tekshirish
            if not captain.team or captain != captain.team.captain:
                return JsonResponse({'error': 'Siz jamoa sardori emassiz'}, status=403)
            
            team = captain.team
            team_name = team.name
            
            # Barcha jamoa a'zolarini solo o'yinchi qilish
            for member in team.members.all():
                member.team = None
                member.registration_type = 'solo'
                member.save()
                # Solo o'yinchi sifatida qayta yaratish
                SoloPlayer.objects.get_or_create(player=member, defaults={'looking_for_team': True})
            
            # Jamoa nomini o'chirish
            team.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Jamoa "{team_name}" muvaffaqiyatli o\'chirildi',
                'team_name': team_name
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Noto\'g\'ri JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LeaveTeamView(View):
    """Jamoa a'zosi tomonidan jamoadan chiqish"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            
            if not user_id:
                return JsonResponse({'error': 'user_id kerak'}, status=400)
            
            # Foydalanuvchini topish
            try:
                player = Player.objects.get(user_id=user_id)
            except Player.DoesNotExist:
                return JsonResponse({'error': 'Foydalanuvchi topilmadi'}, status=404)
            
            # Foydalanuvchi jamoada ekanligini tekshirish
            if not player.team:
                return JsonResponse({'error': 'Siz hech qanday jamoada emassiz'}, status=400)
            
            # Sardor bo'lsa, jamoani o'chirishga ruxsat bermaslik
            if player == player.team.captain:
                return JsonResponse({'error': 'Siz jamoa sardorisiz. Jamoani o\'chirish uchun "Jamoani o\'chirish" tugmasini bosing'}, status=400)
            
            team_name = player.team.name
            
            # Jamoadan chiqish
            player.team = None
            player.registration_type = 'solo'
            player.save()
            
            # Solo o'yinchi sifatida qayta yaratish
            SoloPlayer.objects.get_or_create(player=player, defaults={'looking_for_team': True})
            
            return JsonResponse({
                'success': True,
                'message': f'"{team_name}" jamoasidan muvaffaqiyatli chiqdingiz',
                'team_name': team_name
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Noto\'g\'ri JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


def admin_dashboard(request):
    """Admin dashboard sahifasi"""
    total_players = Player.objects.count()
    total_teams = Team.objects.count()
    solo_players = SoloPlayer.objects.count()
    recent_players = Player.objects.order_by('-created_at')[:10]
    
    context = {
        'total_players': total_players,
        'total_teams': total_teams,
        'solo_players': solo_players,
        'recent_players': recent_players,
    }
    
    return render(request, 'bot_data/dashboard.html', context)