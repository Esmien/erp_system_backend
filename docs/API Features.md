1. Авторизация:

    * POST `/api/v1/auth/register/` Регистрация пользователя
    * PATCH `/api/v1/auth/restore/` Восстановление деактивированного пользователя
    * POST `/api/v1/auth/login/` Вход в систему, выдача JWT-токена
    * POST `/api/v1/auth/logout/` Выход из системы
   
2. Команды

    * GET `/api/v1/teams/{team_id}/` Получить информацию о команде по её ID
    * POST `/api/v1/teams/` Создать новую команду (доступно только менеджерам и админом, изменяется в политиках)
    * POST `/api/v1/teams/join/` Присоединиться к команде по коду приглашения

3. Пользователи

    * GET `/api/v1/users/me/` Получить инфо о себе
    * DELETE `/api/v1/users/me/` 'Мягкое' удаление (деактивация) текущего пользователя
    * PATCH `/api/v1/users/me/` Обновить данные профиля (ФИО)
    * GET `/api/v1/users/me/statistics/` Получить свою статистику оценок

4. Задачи

    * GET `/api/v1/tasks/{task_id}/` Получить информацию о задаче по её ID
    * PATCH `/api/v1/tasks/{task_id}/` Обновить задачу по ID
    * DELETE `/api/v1/tasks/{task_id}/` Удалить задачу по ID
    * GET `/api/v1/tasks/` Получить список задач по фильтрам
    * POST `/api/v1/tasks/` Создать задачу
    * PATCH `/api/v1/tasks/{task_id}/status/` Обновить статус задачи по ID

5. Комментарии

    * GET `/api/v1/tasks/{task_id}/comments/` Получить список комментариев к задаче
    * POST `/api/v1/tasks/{task_id}/comments/` Добавить комментарий к задаче

6. Оценки

    * POST `/api/v1/tasks/{task_id}/evaluation/` Оценить выполнение задачи
    * GET `/api/v1/tasks/{task_id}/evaluation/` Получить оценку за задачу

7. Встречи

    * GET `/api/v1/meetings/` Получить все доступные встречи
    * POST `/api/v1/meetings/` Создать встречу
    * GET `/api/v1/meetings/{meeting_id}/` Получить данные встречи
    * PATCH `/api/v1/meetings/{meeting_id}/` Обновить данные встречи
    * DELETE `/api/v1/meetings/{meeting_id}/` Удалить встречу

8. Календарь

   * GET `/api/v1/calendar/` Получить задачи и встречи на выбранный период